# ============================================================================
# FICHIER : backend/app/services/ticket_workflow.py
# DESCRIPTION : Service de workflow complet pour Composant 0
# ============================================================================

from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import json

from app.models.ticket import Ticket
from app.models.category import Category
from app.models.user import User
from app.services.ai_analyzer import ai_analyzer
from app.services.similarity_detector import similarity_detector


class TicketWorkflow:
    """
    Gestionnaire du workflow complet du Composant 0
    
    Rôle : Transformer un message utilisateur en ticket structuré et validé
    """
    
    async def process_user_message(
        self,
        db: Session,
        message: str,
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Point d'entrée principal du Composant 0
        
        Flux:
        1. Analyse IA du message
        2. Génération Smart Summary
        3. Détection tickets similaires (sans bloquer)
        4. Retour pour validation utilisateur
        
        Args:
            db: Session base de données
            message: Message brut de l'utilisateur
            user_email: Email utilisateur (optionnel)
        
        Returns:
            Dict avec le smart_summary et les actions possibles
        """
        
        # 1. Récupérer les catégories
        categories = self._get_categories(db)
        
        # 2. Analyse IA complète
        ai_analysis = await ai_analyzer.analyze_message_with_smart_summary(
            message=message,
            categories=categories
        )
        
        # 3. Détection tickets similaires (NON BLOQUANT)
        similar_tickets = await similarity_detector.find_similar_tickets(
            db=db,
            message=message,
            category_id=ai_analysis["suggested_category_id"],
            threshold=0.70,
            max_results=5
        )
        
        # 4. Préparer le Smart Summary
        smart_summary = {
            "category": {
                "id": ai_analysis["suggested_category_id"],
                "name": ai_analysis["suggested_category_name"],
                "confidence": ai_analysis["confidence_score"]
            },
            "priority": ai_analysis["suggested_priority"],
            "title": ai_analysis["extracted_title"],
            "symptoms": ai_analysis["extracted_symptoms"],
            "extracted_info": ai_analysis.get("extracted_info", {}),
            "missing_info": ai_analysis.get("missing_info", [])
        }
        
        # 5. Déterminer l'action recommandée
        confidence = ai_analysis["confidence_score"]
        
        if confidence >= 0.85:
            action = "auto_validate"
            message_to_user = "✅ Voici ce que j'ai compris de votre demande :"
        elif confidence >= 0.60:
            action = "confirm_summary"
            message_to_user = "🤔 Voici ce que j'ai compris. Pouvez-vous confirmer ?"
        else:
            action = "ask_clarification"
            message_to_user = "❓ J'ai besoin d'une précision pour bien comprendre votre demande."
        
        return {
            "type": "smart_summary",
            "action": action,
            "message": message_to_user,
            "summary": smart_summary,
            "similar_tickets": similar_tickets,
            "has_similar": len(similar_tickets) > 0,
            "user_email": user_email,
            "original_message": message,
            "analysis_metadata": ai_analysis  # Pour debug/logs
        }
    
    async def create_ticket_after_validation(
        self,
        db: Session,
        validated_summary: Dict,
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Crée le ticket après validation utilisateur
        
        RÈGLE CRITIQUE : Toujours créer le ticket, même si similaires détectés
        
        Args:
            db: Session base de données
            validated_summary: Résumé validé par l'utilisateur
            user_email: Email utilisateur
        
        Returns:
            Dict avec le ticket créé et son ID
        """
        
        # 1. Récupérer l'utilisateur
        user = None
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        
        # 2. Préparer les données du ticket
        category_id = validated_summary["summary"]["category"]["id"]
        title = validated_summary["summary"]["title"]
        symptoms = validated_summary["summary"]["symptoms"]
        priority = validated_summary["summary"]["priority"]
        original_message = validated_summary["original_message"]
        
        # 3. Générer description structurée
        description = self._generate_ticket_description(
            symptoms=symptoms,
            extracted_info=validated_summary["summary"].get("extracted_info", {})
        )
        
        # 4. Préparer similar_tickets JSON
        similar_tickets_data = None
        has_similar = False
        if validated_summary.get("similar_tickets"):
            similar_tickets_data = [
                {
                    "ticket_id": st["id"],
                    "ticket_number": st["ticket_number"],
                    "similarity_score": st["similarity_score"],
                    "title": st["title"]
                }
                for st in validated_summary["similar_tickets"]
            ]
            has_similar = True
        
        # 5. CRÉER LE TICKET (TOUJOURS, sans blocage)
        ticket = Ticket(
            title=title,
            description=description,
            user_message=original_message,
            status="open",
            priority=priority,
            category_id=category_id,
            created_by_user_id=user.id if user else None,
            
            # Analyse IA
            ai_analyzed=True,
            ai_suggested_category_id=category_id,
            ai_confidence_score=validated_summary["summary"]["category"]["confidence"],
            ai_extracted_symptoms=symptoms,
            ai_analysis_metadata=validated_summary.get("analysis_metadata", {}),
            
            # Traçabilité doublons
            similar_tickets=similar_tickets_data,
            has_similar_tickets=has_similar,
            
            # Validation
            user_validated_summary=True,
            validation_method=validated_summary["action"],
            
            # Handoff
            ready_for_L1=True,
            handoff_to_L1_at=datetime.now()
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # 6. Récupérer le nom de la catégorie
        category = db.query(Category).filter(Category.id == category_id).first()
        
        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category_name": category.name if category else "Unknown",
            "created_at": ticket.created_at.isoformat(),
            "has_similar_tickets": has_similar,
            "similar_count": len(similar_tickets_data) if similar_tickets_data else 0,
            "ready_for_L1": ticket.ready_for_L1
        }
    
    async def handle_clarification_response(
        self,
        db: Session,
        original_message: str,
        clarification_response: str,
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Gère la réponse à une question de clarification
        
        Args:
            db: Session base de données
            original_message: Message original
            clarification_response: Réponse de l'utilisateur
            user_email: Email utilisateur
        
        Returns:
            Nouveau smart_summary ou création de ticket
        """
        
        # Combiner les messages
        enriched_message = f"{original_message}\n\nPrécision : {clarification_response}"
        
        # Re-analyser avec le contexte enrichi
        return await self.process_user_message(
            db=db,
            message=enriched_message,
            user_email=user_email
        )
    
    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================
    
    def _get_categories(self, db: Session) -> List[Dict]:
        """
        Récupère toutes les sous-catégories (level 2)
        """
        categories = db.query(Category).filter(Category.level == 2).all()
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "abbreviation": cat.abbreviation,
                "parent_id": cat.parent_id
            }
            for cat in categories
        ]
    
    def _generate_ticket_description(
        self,
        symptoms: List[str],
        extracted_info: Dict
    ) -> str:
        """
        Génère une description structurée du ticket
        """
        description_parts = ["🤖 Ticket créé automatiquement par le Composant 0\n"]
        
        # Symptômes
        description_parts.append("\n📋 **Symptômes identifiés :**")
        for symptom in symptoms:
            description_parts.append(f"  • {symptom}")
        
        # Informations extraites
        if extracted_info:
            description_parts.append("\n\n🔍 **Informations extraites :**")
            for key, value in extracted_info.items():
                if value:
                    description_parts.append(f"  • {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(description_parts)


# Instance globale
ticket_workflow = TicketWorkflow()