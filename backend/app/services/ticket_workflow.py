# ============================================================================
# FICHIER : backend/app/services/ticket_workflow.py
# DESCRIPTION : Service Workflow (Version Corrigée)
# ============================================================================

from requests import session
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

# Helper pour datetime UTC cohérent
def utc_now() -> datetime:
    """Retourne datetime UTC-aware pour éviter les problèmes de timezone"""
    return datetime.now(timezone.utc)


from app.models.ticket import Ticket
from app.models.category import Category
from app.models.user import User
from app.models.analysis_session import AnalysisSession
from app.services.ai_analyzer import ai_analyzer
from app.services.intent_validator import intent_validator
from app.services.context_detector import context_detector
from app.services.suggestion_manager import suggestion_manager, SuggestionContext
from app.core.exceptions import (
    SessionNotFoundError,
    SessionAlreadyConvertedError,
    InvalidUserResponseError,
    AIAnalysisError
)
from app.integrations.glpi_client import get_glpi_client, GLPIClientError
from app.core.config import settings
from app.core.constants import (
    ConfidenceThresholds,
    Messages,
    ModifiableFields,
    SESSION_EXPIRATION_MINUTES,
    MAX_CLARIFICATION_ATTEMPTS,
    MAX_CONVERSATION_TURNS,
    MessageDetection,
    GreetingMessages
)
from app.core.logger import structured_logger


class TicketWorkflow:
    """
    Workflow Composant 0 (Version Corrigée et Renforcée)
    
    Corrections appliquées :
    - ✅ Clarification avec questions ciblées
    - ✅ Modification restreinte (pas de priorité)
    - ✅ Gestion des cas où category = None
    - ✅ Limite de tentatives de clarification
    - ✅ Détection message trop vague
    """
    
    # ========================================================================
    # ÉTAPE 1 : ANALYSE DU MESSAGE
    # ========================================================================
    
    async def analyze_message(
        self,
        db: Session,
        message: str,
        user_email: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        selected_choice_id: Optional[str] = None,
        previous_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        Analyse le message (Version Améliorée - Phase 1)

        Améliorations :
        - ✅ Gestion des cas où confiance < 30% (too_vague)
        - ✅ Compteur de tentatives de clarification
        - ✅ Questions ciblées selon infos manquantes
        - ✅ PHASE 1: Détection salutations et messages non-IT
        """
        structured_logger.log_analysis_started(message, user_email)

        # ====================================================================
        # PHASE 1: DÉTECTION PRÉCOCE DES CAS SPÉCIAUX
        # ====================================================================

        # Détecter les salutations simples (sans contenu IT)
        if MessageDetection.is_greeting_only(message):
            structured_logger.log_error("GREETING_DETECTED", f"Message: {message[:50]}")
            return {
                "type": "greeting_response",
                "action": "greeting",
                "message": GreetingMessages.get("greeting"),  # Message varié
                "summary": None,
                "clarification_attempts": 0,
                "show_examples": True
            }

        # Détecter les messages hors-sujet (non-IT)
        if MessageDetection.is_non_it_message(message):
            structured_logger.log_error("NON_IT_MESSAGE", f"Message: {message[:50]}")
            return {
                "type": "non_it_response",
                "action": "non_it",
                "message": GreetingMessages.get("non_it"),  # Message varié
                "summary": None,
                "clarification_attempts": 0,
                "show_examples": False
            }

        # ====================================================================
        # FIN PHASE 1 - SUITE DU WORKFLOW NORMAL
        # ====================================================================

        # Récupérer le nombre de tentatives précédentes
        attempts = 0
        previous_choice = selected_choice_id
        if parent_session_id:
            parent = db.query(AnalysisSession).filter(
                AnalysisSession.id == parent_session_id
            ).first()
            if parent:
                attempts = parent.clarification_attempts + 1
                if not previous_choice:
                    previous_choice = parent.selected_choice_id
                if not previous_analysis:
                    previous_analysis = parent.ai_summary
        # Vérifier limite de tentatives
        if attempts >= MAX_CLARIFICATION_ATTEMPTS:
            return await self._handle_max_attempts_reached(
                db=db,
                message=message,
                user_email=user_email,
                attempts=attempts
            )
        
        try:
            # Récupérer les catégories (toutes: level 1 + level 2)
            categories = self._get_categories(db)
            subcategories = self._get_subcategories(categories)
            print(f"\nCatégories disponibles : {len(categories)} (dont {len(subcategories)} sous-catégories)")
            if not subcategories:
                raise AIAnalysisError("Aucune catégorie disponible pour l'analyse.")

            # NOUVEAU: Détecter le contexte par mots-clés pour améliorer la classification
            detected_context = context_detector.detect_context(message)

            # Analyse IA (utilise seulement les sous-catégories level 2)
            analysis = await ai_analyzer.analyze_message_with_smart_summary(
                message=message,
                categories=subcategories,
                clarification_attempt=attempts,
                previous_analysis=previous_analysis,
                detected_context=detected_context  # NOUVEAU
            )
            
            confidence = analysis.get("confidence_score", 0.0)
            print("\nRésultat de l'analyse IA :" + str(analysis))
            # CORRECTION : Gérer le cas "too_vague" (confiance < 30%)
            if confidence < ConfidenceThresholds.ASK_CLARIFICATION:
                return await self._handle_too_vague(
                    db=db,
                    message=message,
                    user_email=user_email,
                    attempts=attempts,
                    clarification_question=analysis.get("clarification_question"),
                    previous_choice=previous_choice,
                )
            
            # Déterminer l'action
            action = self._determine_action(confidence)
            
            # CORRECTION : Smart Summary peut avoir category = None
            # Ensure missing_info is always a list (convert string to list if needed)
            missing_info = analysis.get("missing_info", [])
            if isinstance(missing_info, str):
                missing_info = [missing_info] if missing_info else []
            
            smart_summary = {
                "category": {
                    "id": analysis.get("suggested_category_id"),
                    "name": analysis.get("suggested_category_name"),
                    "confidence": confidence
                } if analysis.get("suggested_category_id") else None,
                "priority": analysis.get("suggested_priority"),
                "title": analysis.get("extracted_title"),
                "symptoms": analysis.get("extracted_symptoms", []),
                "extracted_info": analysis.get("extracted_info", {}),
                "missing_info": missing_info,  # NOVO: Always a list
                "clarification_question": analysis.get("clarification_question"),  # NOUVEAU
                "original_message": message
            }
            
            # Créer la session
            session = AnalysisSession(
                ai_summary=smart_summary,
                original_message=message,
                confidence_score=str(confidence),
                status="pending",
                user_email=user_email,
                action_type=action,
                clarification_attempts=attempts,
                parent_session_id=parent_session_id,
                selected_choice_id=selected_choice_id,
                expires_at=utc_now() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            structured_logger.log_analysis_completed(
                session_id=session.id,
                action=action,
                confidence=confidence,
                category=analysis.get("suggested_category_name", "None")
            )
            
            # CORRECTION : Générer message avec questions ciblées
            message_to_user = self._generate_message(
                action=action,
                summary=smart_summary,
                missing_info=analysis.get("missing_info", []),
                attempts=attempts
            )

            # Phase 3: Suggestions intelligentes avec raisonnement
            guided_choices = None
            suggestion_metadata = None

            if action == "ask_clarification":
                # Créer le contexte pour le SuggestionManager
                suggestion_context = SuggestionContext(
                    user_input=message,
                    previous_inputs=[session.original_message] if parent_session_id else [],
                    detected_category=detected_context,
                    confidence_score=confidence,
                    clarification_attempt=attempts,
                    previous_choice_id=previous_choice,
                    ai_clarification_question=analysis.get("clarification_question"),
                    db_categories=categories,
                )

                # Obtenir des suggestions intelligentes avec raisonnement
                suggestion_response = suggestion_manager.get_smart_suggestions(suggestion_context)

                guided_choices = suggestion_response.suggestions
                suggestion_metadata = {
                    "reasoning": suggestion_response.reasoning,
                    "should_regenerate": suggestion_response.should_regenerate,
                    "regeneration_reason": suggestion_response.regeneration_reason,
                    "relevance_score": suggestion_response.relevance_score
                }

            return {
                "session_id": session.id,
                "type": "smart_summary",
                "action": action,
                "message": message_to_user,
                "summary": smart_summary,
                "clarification_attempts": attempts,
                "guided_choices": guided_choices,
                "suggestion_metadata": suggestion_metadata,
                "expires_at": session.expires_at.isoformat()
            }
            
        except Exception as e:
            structured_logger.log_error("AI_ANALYSIS", str(e))
            raise AIAnalysisError(f"Erreur lors de l'analyse: {str(e)}")
    
    # ========================================================================
    # GESTION DES CAS LIMITES
    # ========================================================================
    
    async def _handle_too_vague(
        self,
        db: Session,
        message: str,
        user_email: Optional[str],
        attempts: int,
        clarification_question: Optional[str] = None,
        previous_choice: Optional[str] = None,
    ) -> Dict:
        """
        Gère le cas où le message est trop vague (confidence < 30%)

        Phase 2 : Ajout de choix guidés cliquables
        """
        print("\n clarification_question (inside function too_vague):", clarification_question)
        session = AnalysisSession(
            ai_summary=None,
            original_message=message,
            confidence_score="0.0",
            status="too_vague",
            user_email=user_email,
            action_type="too_vague",
            clarification_attempts=attempts,
            expires_at=utc_now() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        # Phase 3: Suggestions intelligentes avec raisonnement
        detected_context = context_detector.detect_context(message)

        # Créer le contexte pour le SuggestionManager
        suggestion_context = SuggestionContext(
            user_input=message,
            previous_inputs=[],
            detected_category=detected_context,
            confidence_score=0.0,  # Confiance nulle pour too_vague
            clarification_attempt=attempts,
            previous_choice_id=previous_choice,
            ai_clarification_question=clarification_question,
            db_categories=self._get_categories(db),
        )

        # Obtenir des suggestions intelligentes avec raisonnement
        suggestion_response = suggestion_manager.get_smart_suggestions(suggestion_context)

        guided_choices = suggestion_response.suggestions
        suggestion_metadata = {
            "reasoning": suggestion_response.reasoning,
            "should_regenerate": suggestion_response.should_regenerate,
            "regeneration_reason": suggestion_response.regeneration_reason,
            "relevance_score": suggestion_response.relevance_score
        }

        # Phase 2: Message adapté avec indication des choix
        message_to_user = context_detector.get_clarification_message(
            attempt=attempts,
            detected_context=detected_context,
        )

        # Ajouter la question IA en complément si disponible
        if clarification_question and attempts > 0:
            message_to_user += f"\n\n💬 *{clarification_question}*"

        return {
            "session_id": session.id,
            "type": "smart_summary",
            "action": "too_vague",
            "message": message_to_user,
            "summary": None,
            "suggestion_metadata": suggestion_metadata,
            "clarification_attempts": attempts,
            "guided_choices": guided_choices,
            "expires_at": session.expires_at.isoformat()
        }
    
    async def _handle_max_attempts_reached(
        self,
        db: Session,
        message: str,
        user_email: Optional[str],
        attempts: int
    ) -> Dict:
        """
        Gère gracieusement le cas où l'utilisateur a dépassé le nombre max de tentatives

        PHASE 1 - Amélioration:
        - Message empathique et rassurant
        - Pas d'erreur/crash, création ticket automatique
        - Escalade vers technicien humain avec priorité haute

        Action : Créer un ticket avec catégorie générique + escalade L2
        """
        structured_logger.log_error(
            "MAX_ATTEMPTS_REACHED",
            f"Attempts: {attempts}, User: {user_email}, Message: {message[:50]}"
        )
        # Catégorie par défaut : "Non catégorisé"
        default_category = db.query(Category).filter(
            Category.abbreviation == "99-non-cat"
        ).first()
        
        if not default_category:
            # Créer la catégorie si elle n'existe pas
            default_category = Category(
                name="Non catégorisé",
                abbreviation="99-non-cat",
                level=1,
                description="Tickets nécessitant clarification humaine"
            )
            db.add(default_category)
            db.commit()
            db.refresh(default_category)
        
        # Créer ticket avec priorité haute (nécessite attention)
        user = None
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        
        ticket = Ticket(
            ticket_number=self.generate_ticket_number(db),
            title=f"Demande nécessitant clarification : {message[:50]}...",
            description=(
                f"🤖 Ticket créé automatiquement après {attempts} tentatives de clarification.\n\n"
                f"**Message utilisateur :**\n{message}\n\n"
                f"**Raison :** Le chatbot n'a pas pu comprendre la demande après plusieurs échanges.\n"
                f"**Action requise :** Un technicien doit contacter l'utilisateur pour clarifier."
            ),
            user_message=message,
            status="open",
            priority="high",  # Haute priorité car bloque l'utilisateur
            category_id=default_category.id,
            created_by_user_id=user.id if user else None,
            ai_confidence_score=0.0,
            ai_extracted_symptoms=[],
            validation_method="max_attempts_escalation",
            ready_for_l1=False,  # Escalade directe L2
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # PHASE 1: Message empathique et informatif (avec variation)
        friendly_message = GreetingMessages.get(
            "max_attempts",
            ticket_number=ticket.ticket_number
        )

        structured_logger.log_ticket_created(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            session_id=None,
            validation_method="max_attempts_escalation"
        )

        return {
            "type": "ticket_created",
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_name": default_category.name,
            "created_at": ticket.created_at.isoformat(),
            "ready_for_L1": False,
            "escalated_to_human": True,  # NOUVEAU FLAG
            "message": friendly_message
        }
    
    # ========================================================================
    # ACTIONS UTILISATEUR (Corrigées)
    # ========================================================================
    
    async def handle_confirm_summary(
        self,
        db: Session,
        session_id: str,
        user_action: str,
        modifications: Optional[Dict] = None
    ) -> Dict:
        """
        Gère CONFIRM_SUMMARY (Version Corrigée)
        
        CORRECTION : Filtre les modifications interdites
        """
        session = self._get_valid_session(db, session_id)
        summary = session.ai_summary
        
        if user_action == "confirm":
            pass  # Utiliser tel quel
        
        elif user_action == "modify":
            if modifications:
                # CORRECTION : Filtrer les champs autorisés
                allowed_mods = ModifiableFields.validate_modifications(modifications)
                
                if not allowed_mods:
                    raise InvalidUserResponseError(Messages.ERROR_INVALID_MODIFICATION)
                
                # Appliquer seulement les modifications autorisées
                if "title" in allowed_mods:
                    summary["title"] = allowed_mods["title"]
                
                if "symptoms" in allowed_mods:
                    summary["symptoms"] = allowed_mods["symptoms"]
                
                structured_logger.log_error(
                    "MODIFICATIONS_APPLIED",
                    f"session={session_id}, fields={list(allowed_mods.keys())}"
                )
        
        else:
            raise InvalidUserResponseError("Action invalide: 'confirm' ou 'modify'")
        
        # Créer le ticket
        ticket = await self._create_ticket(
            db=db,
            summary=summary,
            user_email=session.user_email,
            validation_method=f"confirm_summary_{user_action}"
        )
        
        # Invalider session
        session.status = "converted_to_ticket"
        session.ticket_id = str(ticket["ticket_id"])
        session.conversion_at = utc_now()
        db.commit()

        structured_logger.log_ticket_created(
            ticket_id=ticket["ticket_id"],
            ticket_number=ticket["ticket_number"],
            session_id=session_id,
            validation_method=f"confirm_{user_action}"
        )
        
        return ticket
    
    async def handle_clarification(
        self,
        db: Session,
        session_id: str,
        clarification_response: str,
        selected_choice_id: Optional[str] = None
    ) -> Dict:
        """
        Gère ASK_CLARIFICATION (Version Corrigée - Fix stabilité + Topic Shift)

        Phase 3 :
        - ✅ Passe le session_id pour tracking des tentatives
        - ✅ Propage selected_choice_id pour choix guidés contextuels
        - ✅ Transmet previous_analysis pour persistance du contexte IA

        FIX CRITIQUE:
        - ✅ N'invalide la session qu'APRÈS succès de l'analyse
        - ✅ En cas d'erreur, la session reste utilisable pour retry

        NOUVEAU - TOPIC SHIFT:
        - ✅ Détecte si l'utilisateur change de sujet
        - ✅ Si topic shift: propose de choisir OU traite le nouveau sujet
        - ✅ Évite la fusion incohérente de contextes
        """
        session = self._get_valid_session(db, session_id)
        original_message = session.original_message
        previous_analysis = session.ai_summary  # Phase 3: capturer avant invalidation
        user_email = session.user_email  # Capturer avant commit potentiel

        # Stocker le choice_id sur la session (mais ne pas invalider encore)
        if selected_choice_id:
            session.selected_choice_id = selected_choice_id
            db.commit()

        # ================================================================
        # NOUVEAU: Détection de changement de sujet (Topic Shift)
        # ================================================================
        topic_shift = context_detector.detect_topic_shift(
            original_message=original_message,
            clarification_response=clarification_response
        )

        if topic_shift["is_topic_shift"]:
            structured_logger.log_error(
                "TOPIC_SHIFT_DETECTED",
                f"Original: {topic_shift['original_context']} → New: {topic_shift['new_context']}"
            )

            if topic_shift["recommendation"] == "replace":
                # Changement radical de sujet → traiter comme NOUVEAU problème
                # Invalider l'ancienne session et repartir de zéro
                session.status = "invalidated"
                session.invalidation_reason = "topic_shift_replaced"
                db.commit()

                # Analyser le nouveau message seul (pas de fusion)
                return await self.analyze_message(
                    db=db,
                    message=clarification_response,  # Seulement le nouveau message
                    user_email=user_email,
                    parent_session_id=None,  # Pas de parent, c'est un nouveau départ
                    selected_choice_id=None,
                    previous_analysis=None
                )

            elif topic_shift["recommendation"] == "ask_user":
                # Sujets potentiellement liés → demander à l'utilisateur
                # Créer une session spéciale pour gérer le topic shift
                shift_session = AnalysisSession(
                    ai_summary={
                        "topic_shift": True,
                        "original_context": topic_shift["original_context"],
                        "new_context": topic_shift["new_context"],
                        "original_message": original_message,
                        "clarification_response": clarification_response
                    },
                    original_message=original_message,
                    confidence_score="0.0",
                    status="pending_topic_choice",
                    user_email=user_email,
                    action_type="topic_shift",
                    clarification_attempts=session.clarification_attempts,
                    parent_session_id=session_id,
                    expires_at=utc_now() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)
                )

                db.add(shift_session)
                db.commit()
                db.refresh(shift_session)

                return {
                    "session_id": shift_session.id,
                    "type": "topic_shift",
                    "action": "topic_shift",
                    "message": context_detector.get_topic_shift_message(
                        topic_shift["original_context"],
                        topic_shift["new_context"]
                    ),
                    "summary": None,
                    "clarification_attempts": session.clarification_attempts,
                    "guided_choices": context_detector.get_topic_shift_choices(),
                    "expires_at": shift_session.expires_at.isoformat()
                }

        # ================================================================
        # PAS DE TOPIC SHIFT → Comportement normal (fusion du contexte)
        # ================================================================
        enriched_message = f"{original_message}\n\nPrécision : {clarification_response}"

        try:
            # Tenter l'analyse AVANT d'invalider
            result = await self.analyze_message(
                db=db,
                message=enriched_message,
                user_email=user_email,
                parent_session_id=session_id,
                selected_choice_id=selected_choice_id,
                previous_analysis=previous_analysis
            )

            # Succès ! Maintenant on peut invalider la session
            session.status = "invalidated"
            session.invalidation_reason = "clarification_provided"
            db.commit()

            return result

        except Exception as e:
            # En cas d'erreur, la session reste valide pour un retry
            structured_logger.log_error(
                "CLARIFICATION_FAILED",
                f"Session {session_id} kept valid after error: {str(e)}"
            )
            raise

    async def handle_topic_shift_choice(
        self,
        db: Session,
        session_id: str,
        choice: str  # "keep_new", "keep_old", "both_problems"
    ) -> Dict:
        """
        Gère le choix de l'utilisateur suite à un topic shift détecté.

        - keep_new: Traiter le nouveau problème
        - keep_old: Revenir au problème original
        - both_problems: Créer un ticket avec les deux problèmes mentionnés
        """
        session = self._get_valid_session(db, session_id)

        if session.action_type != "topic_shift":
            raise InvalidUserResponseError("Cette session n'est pas en attente d'un choix de sujet.")

        topic_data = session.ai_summary
        original_message = topic_data.get("original_message", "")
        clarification_response = topic_data.get("clarification_response", "")

        # Invalider la session de topic shift
        session.status = "invalidated"
        session.invalidation_reason = f"topic_shift_resolved_{choice}"
        db.commit()

        if choice == "keep_new":
            # Traiter seulement le nouveau problème
            return await self.analyze_message(
                db=db,
                message=clarification_response,
                user_email=session.user_email,
                parent_session_id=None,
                selected_choice_id=None,
                previous_analysis=None
            )

        elif choice == "keep_old":
            # Revenir au problème original
            return await self.analyze_message(
                db=db,
                message=original_message,
                user_email=session.user_email,
                parent_session_id=None,
                selected_choice_id=None,
                previous_analysis=None
            )

        elif choice == "both_problems":
            # L'utilisateur a vraiment deux problèmes → les mentionner explicitement
            combined_message = (
                f"J'ai deux problèmes à signaler :\n"
                f"1. {original_message}\n"
                f"2. {clarification_response}"
            )
            return await self.analyze_message(
                db=db,
                message=combined_message,
                user_email=session.user_email,
                parent_session_id=None,
                selected_choice_id=None,
                previous_analysis=None
            )

        else:
            raise InvalidUserResponseError(f"Choix invalide: {choice}")

    # Les autres méthodes (handle_auto_validate, _create_ticket) 

    async def handle_auto_validate(
        self,
        db: Session,
        session_id: str,
        user_response: str
    ) -> Dict:
        """
        Gère l'action AUTO_VALIDATE avec validation d'intention
        
        Améliorations :
        - Récupère les données depuis la session (pas du frontend)
        - Validation intelligente de la réponse
        - Idempotence garantie
        """
        # 1. Récupérer la session (Source de vérité)
        session = self._get_valid_session(db, session_id)
        
        # 2. Validation intelligente de l'intention
        if not intent_validator.validate_positive_intent(user_response):
            structured_logger.log_invalid_response(session_id, user_response)
            raise InvalidUserResponseError(Messages.ERROR_INVALID_RESPONSE)
        
        # 3. Créer le ticket depuis les données SÉCURISÉES
        ticket = await self._create_ticket(
            db=db,
            summary=session.ai_summary,
            user_email=session.user_email,
            validation_method="auto_validate"
        )
        
        # 4. Invalider la session (Idempotence)
        session.status = "converted_to_ticket"
        session.ticket_id = str(ticket["ticket_id"])
        session.conversion_at = utc_now()
        db.commit()

        structured_logger.log_ticket_created(
            ticket_id=ticket["ticket_id"],
            ticket_number=ticket["ticket_number"],
            session_id=session_id,
            validation_method="auto_validate"
        )
        
        return ticket
    
    # ========================================================================
    # UTILITAIRES
    # ========================================================================
    
    def _determine_action(self, confidence: float) -> str:
        """Détermine l'action basée sur la confiance"""
        if confidence >= ConfidenceThresholds.AUTO_VALIDATE:
            return "auto_validate"
        elif confidence >= ConfidenceThresholds.CONFIRM_SUMMARY:
            return "confirm_summary"
        elif confidence >= ConfidenceThresholds.ASK_CLARIFICATION:
            return "ask_clarification"
        else:
            return "too_vague"
    
    def _generate_message(
        self,
        action: str,
        summary: Dict,
        missing_info: List[str] = None,
        attempts: int = 0
    ) -> str:
        """
        Génère le message utilisateur (Version Professionnelle)

        AMÉLIORATIONS:
        - ✅ Messages variés (sélection aléatoire)
        - ✅ Messages plus courts
        - ✅ Contexte-aware (évite répétitions si attempts > 0)
        """
        if action == "auto_validate":
            return Messages.get("auto_validate", summary=self._format_summary_display(summary))

        elif action == "confirm_summary":
            return Messages.get("confirm_summary", summary=self._format_summary_display(summary))

        elif action == "ask_clarification":
            # Utiliser la question de clarification de l'analyse IA
            clarification_question = summary.get("clarification_question",
                                                  "Pouvez-vous fournir plus de détails ?")

            # CONTEXT-AWARE: Si c'est une tentative suivante, message plus court
            if attempts > 0:
                # On ne répète pas le contexte, juste la question
                return f"🔍 **Encore une précision :**\n\n{clarification_question}"

            return Messages.get("ask_clarification", missing_info_list=clarification_question)

        elif action == "too_vague":
            return Messages.get("too_vague")

        return "Message par défaut"

    def _format_summary_display(self, summary: Dict) -> str:
        """
        Formatte le résumé pour affichage (Version Compacte)

        AMÉLIORATION: Format plus court et lisible
        """
        parts = []

        # Ligne compacte: Catégorie + Priorité
        cat_name = summary.get("category", {}).get("name") if summary.get("category") else None
        priority = summary.get("priority", "").upper() if summary.get("priority") else None

        if cat_name and priority:
            parts.append(f"📋 {cat_name} • 🎯 {priority}")
        elif cat_name:
            parts.append(f"📋 {cat_name}")
        elif priority:
            parts.append(f"🎯 {priority}")

        # Titre
        if summary.get("title"):
            parts.append(f"📝 {summary['title']}")

        # Symptômes (max 3 pour rester court)
        symptoms = summary.get("symptoms", [])
        if symptoms:
            symptoms_display = symptoms[:3]  # Max 3 symptômes
            parts.append("**Symptômes** : " + ", ".join(symptoms_display))
            if len(symptoms) > 3:
                parts.append(f"  _(+{len(symptoms) - 3} autres)_")

        return "\n".join(parts) if parts else "Analyse en cours..."
    
    # Autres méthodes utilitaires identiques...
    def _get_valid_session(self, db: Session, session_id: str) -> AnalysisSession:
        """
        Récupère une session valide
        
        Vérifie :
        - Session existe
        - Pas expirée
        - Pas déjà convertie (idempotence)
        """
        session = db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id
        ).first()
        
        if not session:
            structured_logger.log_session_expired(session_id)
            raise SessionNotFoundError(Messages.ERROR_SESSION_NOT_FOUND)
        
        # Vérifier expiration (comparer en UTC)
        # Gère les cas où expires_at peut être naive ou aware
        session_expiry = session.expires_at
        if session_expiry.tzinfo is None:
            # Si naive, on assume que c'est UTC (pour compatibilité avec anciennes sessions)
            session_expiry = session_expiry.replace(tzinfo=timezone.utc)

        if session_expiry < utc_now():
            session.status = "expired"
            db.commit()
            structured_logger.log_session_expired(session_id)
            raise SessionNotFoundError(Messages.ERROR_SESSION_NOT_FOUND)
        
        # Vérifier si déjà convertie (idempotence)
        if session.status == "converted_to_ticket":
            structured_logger.log_session_already_used(session_id)
            raise SessionAlreadyConvertedError(Messages.ERROR_SESSION_ALREADY_USED)
        
        return session
    
    def _get_categories(self, db: Session) -> List[Dict]:
        """Récupère toutes les catégories actives (level 1 + level 2)"""
        categories = db.query(Category).filter(Category.is_active == True).all()
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "abbreviation": cat.abbreviation,
                "parent_id": cat.parent_id,
                "level": cat.level,
                "is_active": cat.is_active,
            }
            for cat in categories
        ]

    @staticmethod
    def _get_subcategories(categories: List[Dict]) -> List[Dict]:
        """Filtre les sous-catégories (level 2) pour l'AI analyzer"""
        return [c for c in categories if c.get("level") == 2]
    
    def _generate_description(self, symptoms: List[str], extracted_info: Dict) -> str:
        """Génère une description structurée"""
        parts = ["🤖 Ticket créé automatiquement\n"]
        
        parts.append("\n📋 **Symptômes** :")
        for symptom in symptoms:
            parts.append(f"  • {symptom}")
        
        if extracted_info:
            parts.append("\n\n🔍 **Informations extraites** :")
            for key, value in extracted_info.items():
                if value:
                    parts.append(f"  • {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(parts)

    async def _create_ticket(
        self,
        db: Session,
        summary: Dict,
        user_email: Optional[str],
        validation_method: str
    ) -> Dict:
        """
        Crée le ticket (VERSION MODIFIÉE AVEC GLPI)
        """
        # Récupérer l'utilisateur
        user = None
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        
        # Extraire les données
        category_id = summary["category"]["id"] if summary.get("category") else None
        title = summary.get("title", "Ticket sans titre")
        symptoms = summary.get("symptoms", [])
        priority = summary.get("priority", "medium")
        original_message = summary.get("original_message", "")
        
        # Générer description
        description = self._generate_description(
            symptoms=symptoms,
            extracted_info=summary.get("extracted_info", {})
        )
        
        # ====================================================================
        # CRÉATION DANS GLPI (SI ACTIVÉ)
        # ====================================================================
        
        glpi_ticket_id = None
        glpi_sync_at = None
        
        if settings.GLPI_ENABLED:
            try:
                glpi_client = get_glpi_client()
                
                # Créer le ticket dans GLPI
                glpi_ticket = glpi_client.create_ticket(
                    title=title,
                    description=f"{description}\n\n---\nMessage original:\n{original_message}",
                    category_id=category_id,
                    priority=priority,
                    user_email=user_email
                )
                
                t = glpi_ticket.get("id")
                glpi_sync_at = utc_now()
                
                structured_logger.log_error(
                    "GLPI_TICKET_CREATED",
                    f"Ticket GLPI créé: ID={glpi_ticket_id}"
                )
                
                # Ajouter un suivi IA dans GLPI
                if glpi_ticket_id:
                    ai_analysis_summary = (
                        f"🤖 Analyse IA:\n"
                        f"- Confiance: {summary.get('category', {}).get('confidence', 0) * 100:.0f}%\n"
                        f"- Méthode de validation: {validation_method}\n"
                        f"- Symptômes: {', '.join(symptoms)}"
                    )
                    
                    glpi_client.add_followup(
                        ticket_id=glpi_ticket_id,
                        content=ai_analysis_summary,
                        is_private=True  # Suivi privé pour les techniciens
                    )
                
            except GLPIClientError as e:
                structured_logger.log_error("GLPI_SYNC_ERROR", str(e))
                # Ne pas bloquer la création si GLPI échoue
                if settings.GLPI_SYNC_MODE == "glpi_only":
                    raise Exception(f"Impossible de créer le ticket dans GLPI: {str(e)}")
        
        # ====================================================================
        # CRÉATION DANS NOTRE BASE DE DONNÉES
        # ====================================================================
        
        ticket = Ticket(
            ticket_number=self.generate_ticket_number(db),
            title=title,
            description=description,
            user_message=original_message,
            status="open",
            priority=priority,
            category_id=None ,#if category_id is str else category_id,
            created_by_user_id=user.id if user else None,
            
            # IA
            # ai_analyzed=True,
            # ai_suggested_category_id=category_id,
            ai_confidence_score=summary.get("category", {}).get("confidence", 0.0),
            ai_extracted_symptoms=symptoms,
            # ai_analysis_metadata=summary,
            
            # Validation
            # user_validated_summary=True,
            validation_method=validation_method,
            
            # Handoff
            ready_for_l1=True,
            # handoff_to_l1_at=datetime.now(),
            
            # GLPI
            glpi_ticket_id=glpi_ticket_id,
            synced_to_glpi=glpi_ticket_id is not None,
            glpi_sync_at=glpi_sync_at,
            # glpi_status=1 if glpi_ticket_id else None  # 1 = Nouveau
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Récupérer nom catégorie
        category = db.query(Category).filter(Category.id == category_id).first() if category_id else None
        
        # Message personnalisé
        if glpi_ticket_id:
            message = (
                f"✅ **Ticket créé avec succès !**\n\n"
                f"📋 Numéro: {ticket.ticket_number}\n"
                f"🔗 GLPI ID: {glpi_ticket_id}\n"
                f"📁 Catégorie: {category.name if category else 'N/A'}\n"
                f"🎯 Priorité: {priority.upper()}\n\n"
                f"🔍 Recherche de solutions en cours..."
            )
        else:
            message = Messages.TICKET_CREATED_MESSAGE.format(
                ticket_number=ticket.ticket_number,
                category=category.name if category else "Unknown",
                priority=priority.upper()
            )
        
        return {
            "type": "ticket_created",
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "glpi_ticket_id": glpi_ticket_id,
            "title": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_name": category.name if category else "Unknown",
            "created_at": ticket.created_at.isoformat(),
            "ready_for_L1": ticket.ready_for_l1,
            "synced_to_glpi": ticket.synced_to_glpi,
            "message": message
        }
# funtion moved to utils/ticket_utils.py
    @staticmethod
    def generate_ticket_number(db):
        """
        Génère un numéro de ticket unique : TKT-YYYY-NNNNN
        """
        current_year = datetime.now().year
        last_ticket = db.query(Ticket).filter(
            Ticket.ticket_number.like(f'TKT-{current_year}-%')
        ).order_by(Ticket.id.desc()).first()
        
        if last_ticket:
            seq_num = int(last_ticket.ticket_number.split('-')[-1]) + 1
        else:
            seq_num = 1
        
        ticket_number = f"TKT-{current_year}-{seq_num:05d}"
        # ALSO REMOVE: db.close()  <-- Don't close the session here!
        return ticket_number
# Instance globale
ticket_workflow = TicketWorkflow()