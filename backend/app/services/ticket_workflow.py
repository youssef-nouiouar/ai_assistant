# ============================================================================
# FICHIER : backend/app/services/ticket_workflow.py
# DESCRIPTION : Service Workflow (Version Corrigée)
# ============================================================================

from sqlalchemy import text
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
from app.services.category_display import get_main_choices
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

        # Récupérer le nombre de tentatives précédentes + historique conversation
        attempts = 0
        previous_choice = selected_choice_id
        conversation_history = [{"role": "user", "content": message}]
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
                # Construire l'historique de conversation.
                # On stocke uniquement la clarification brute (ce que l'utilisateur
                # a tapé) dans l'historique — pas le message enrichi complet — pour
                # éviter une croissance O(n²) du nombre de tokens envoyés au LLM.
                # La variable `message` (enriched) reste utilisée pour l'analyse.
                conversation_history = list(parent.conversation_history or [])
                prev_question = (parent.ai_summary or {}).get("response_message")
                if prev_question:
                    conversation_history.append({"role": "assistant", "content": prev_question})
                # Extract only the new part added by this clarification round.
                # Format of enriched message: "{root}\n\nPrécision : {raw}"
                if "\n\nPrécision : " in message:
                    raw_turn = message.rsplit("\n\nPrécision : ", 1)[-1]
                else:
                    raw_turn = message
                conversation_history.append({"role": "user", "content": raw_turn})
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

            # Analyse IA (utilise seulement les sous-catégories level 2)
            analysis = await ai_analyzer.analyze_message_with_smart_summary(
                message=message,
                categories=subcategories,
                previous_analysis=previous_analysis,
                conversation_history=conversation_history
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
                    analysis=analysis,
                    categories=categories,
                    conversation_history=conversation_history,
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
                "missing_info": missing_info,
                "response_message": analysis.get("response_message"),
                "original_message": message
            }
            
            # Créer la session
            session = AnalysisSession(
                ai_summary=smart_summary,
                original_message=message,
                confidence_score=confidence,
                status="pending",
                user_email=user_email,
                action_type=action,
                clarification_attempts=attempts,
                parent_session_id=parent_session_id,
                selected_choice_id=selected_choice_id,
                conversation_history=conversation_history,
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
            
            message_to_user = self._generate_message(
                action=action,
                summary=smart_summary,
                missing_info=analysis.get("missing_info", []),
            )

            # AI-generated choices for ask_clarification
            guided_choices = None
            ai_choices = analysis.get("suggested_choices")
            if ai_choices and isinstance(ai_choices, list) and action == "ask_clarification":
                guided_choices = self._format_ai_choices(ai_choices)

            return {
                "session_id": session.id,
                "type": "smart_summary",
                "action": action,
                "message": message_to_user,
                "summary": smart_summary,
                "clarification_attempts": attempts,
                "guided_choices": guided_choices,
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
        analysis: Optional[Dict] = None,
        categories: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Gère le cas où le message est trop vague (confidence < 30%)

        Phase 2 : Ajout de choix guidés cliquables
        """
        analysis = analysis or {}
        ai_message = analysis.get("response_message")
        session = AnalysisSession(
            ai_summary={"response_message": ai_message} if ai_message else None,
            original_message=message,
            confidence_score="0.0",
            status="too_vague",
            user_email=user_email,
            action_type="too_vague",
            clarification_attempts=attempts,
            conversation_history=conversation_history or [],
            expires_at=utc_now() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        # Use AI-generated choices if available, fallback to DB categories
        ai_choices = analysis.get("suggested_choices")
        if ai_choices and isinstance(ai_choices, list):
            guided_choices = self._format_ai_choices(ai_choices)
        else:
            all_categories = categories or self._get_categories(db)
            guided_choices = get_main_choices(all_categories)

        # Use AI-generated message if available, fallback to templates
        if ai_message:
            message_to_user = ai_message
        else:
            message_to_user = context_detector.get_clarification_message(
                attempt=attempts,
                detected_context=None,
            )

        return {
            "session_id": session.id,
            "type": "smart_summary",
            "action": "too_vague",
            "message": message_to_user,
            "summary": None,
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
            "glpi_ticket_id": None,
            "title": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_name": default_category.name,
            "created_at": ticket.created_at.isoformat(),
            "ready_for_L1": False,
            "synced_to_glpi": False,
            "escalated_to_human": True,
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
                
                structured_logger.log_info(
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
        Gère ASK_CLARIFICATION

        - Passe le session_id pour tracking des tentatives
        - Propage selected_choice_id pour choix guidés contextuels
        - Transmet previous_analysis pour persistance du contexte IA
        - N'invalide la session qu'APRÈS succès de l'analyse (retry-safe)
        """
        session = self._get_valid_session(db, session_id)
        original_message = session.original_message
        previous_analysis = session.ai_summary  # Phase 3: capturer avant invalidation
        user_email = session.user_email  # Capturer avant commit potentiel

        # Stocker le choice_id sur la session (mais ne pas invalider encore)
        if selected_choice_id:
            session.selected_choice_id = selected_choice_id
            db.commit()

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

    # Les autres méthodes (handle_auto_validate, _create_ticket)

    async def handle_restart_from(
        self,
        db: Session,
        session_id: str,
        edited_message: str,
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Invalide la session courante et relance l'analyse depuis le message modifié.
        Utilisé quand l'utilisateur édite un message précédent (Issue 4B).
        """
        session = self._get_valid_session(db, session_id)
        if not user_email:
            user_email = session.user_email

        session.status = "invalidated"
        session.invalidation_reason = "user_edited_message"
        db.commit()

        return await self.analyze_message(
            db=db,
            message=edited_message,
            user_email=user_email,
            parent_session_id=None,
            selected_choice_id=None,
            previous_analysis=None
        )

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
    
    @staticmethod
    def _format_ai_choices(ai_choices: list) -> List[Dict]:
        """Convertit les choix IA en format guided_choices pour le frontend."""
        return [
            {"id": f"dynamic_{i}", "label": c.get("label", ""), "icon": c.get("icon", "📋")}
            for i, c in enumerate(ai_choices)
        ]

    def _generate_message(
        self,
        action: str,
        summary: Dict,
        missing_info: List[str] = None,
    ) -> str:
        """
        Génère le message utilisateur.

        Règle : confirm_summary et auto_validate utilisent toujours le template
        (le message IA peut contenir des questions inappropriées pour ces actions).
        Le message IA est réservé à ask_clarification et too_vague.
        """
        ai_message = summary.get("response_message") if summary else None

        if action == "auto_validate":
            return Messages.get("auto_validate")

        elif action == "confirm_summary":
            return Messages.get("confirm_summary")

        elif action == "ask_clarification":
            return ai_message if ai_message else Messages.get(
                "ask_clarification", missing_info_list="Pouvez-vous fournir plus de détails ?"
            )

        elif action == "too_vague":
            return ai_message if ai_message else Messages.get("too_vague")

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
                
                # Récupérer le glpi_user_id depuis notre table Users
                glpi_user_id = user.glpi_user_id if user else None
                
                # Créer le ticket dans GLPI
                glpi_ticket = await glpi_client.create_ticket(
                    title=title,
                    description=f"{description}\n\n---\nMessage original:\n{original_message}",
                    category_id=category_id,
                    priority=priority,
                    user_email=user_email,
                    requester_id=glpi_user_id
                )
                
                glpi_ticket_id = glpi_ticket.get("id")
                glpi_sync_at = utc_now()
                
                structured_logger.log_info(
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
                    
                    await glpi_client.add_followup(
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
            category_id=category_id,
            created_by_user_id=user.id if user else None,
            ai_confidence_score=summary.get("category", {}).get("confidence", 0.0),
            ai_extracted_symptoms=symptoms,
            validation_method=validation_method,
            ready_for_l1=True,
            glpi_ticket_id=glpi_ticket_id,
            synced_to_glpi=glpi_ticket_id is not None,
            glpi_sync_at=glpi_sync_at,
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
    @staticmethod
    def generate_ticket_number(db):
        """
        Génère un numéro de ticket unique : TKT-YYYY-NNNNN

        Thread-safe via PostgreSQL advisory lock (transaction-level).
        The lock (key 20250001) is held until the enclosing transaction
        commits or rolls back, so no two concurrent requests can read
        the same MAX sequence and produce a duplicate number.
        """
        db.execute(text("SELECT pg_advisory_xact_lock(20250001)"))

        current_year = datetime.now().year
        last_ticket = db.query(Ticket).filter(
            Ticket.ticket_number.like(f'TKT-{current_year}-%')
        ).order_by(Ticket.id.desc()).first()

        seq_num = int(last_ticket.ticket_number.split('-')[-1]) + 1 if last_ticket else 1
        return f"TKT-{current_year}-{seq_num:05d}"
# Instance globale
ticket_workflow = TicketWorkflow()