# ============================================================================
# FICHIER : backend/app/services/ticket_service.py
# DESCRIPTION : Service de gestion des tickets
# ============================================================================

from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from app.models.ticket import Ticket
from app.models.category import Category
from app.models.user import User
from app.services.ai_analyzer import ai_analyzer

class TicketService:
    """
    Service de gestion des tickets
    """
    
    async def create_ticket_from_message(
        self, 
        db: Session, 
        message: str, 
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Crée un ticket depuis un message utilisateur
        
        Args:
            db: Session de base de données
            message: Message de l'utilisateur
            user_email: Email de l'utilisateur (optionnel)
        
        Returns:
            Dict contenant le ticket créé et l'analyse IA
        """
        
        # 1. Récupérer toutes les sous-catégories (level 2)
        categories = db.query(Category).filter(Category.level == 2).all()
        categories_list = [
            {
                "id": cat.id,
                "name": cat.name,
                "abbreviation": cat.abbreviation
            }
            for cat in categories
        ]
        
        # 2. Analyser le message avec l'IA
        ai_analysis = await ai_analyzer.analyze_message(message, categories_list)
        
        # 3. Récupérer l'utilisateur si email fourni
        user = None
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        
        # 4. Créer le ticket
        ticket = Ticket(
            title=ai_analysis["title"],
            user_message=message,
            description=f"Ticket créé automatiquement depuis le chatbot.\n\nSymptômes identifiés:\n" + \
                       "\n".join(f"- {s}" for s in ai_analysis["symptoms"]),
            status="open",
            priority=ai_analysis["priority"],
            category_id=ai_analysis["category_id"],
            created_by_user_id=user.id if user else None,
            ai_analyzed=True,
            ai_suggested_category_id=ai_analysis["category_id"],
            ai_confidence_score=ai_analysis["confidence_score"],
            ai_extracted_symptoms=ai_analysis["symptoms"],
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # 5. Récupérer le nom de la catégorie
        category = db.query(Category).filter(Category.id == ticket.category_id).first()
        
        return {
            "ticket": ticket,
            "category_name": category.name if category else "Unknown",
            "ai_analysis": ai_analysis
        }
    
    def get_ticket_by_id(self, db: Session, ticket_id: int) -> Optional[Ticket]:
        """
        Récupère un ticket par son ID
        """
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    def get_ticket_by_number(self, db: Session, ticket_number: str) -> Optional[Ticket]:
        """
        Récupère un ticket par son numéro
        """
        return db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    
    def get_tickets(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Ticket]:
        """
        Récupère une liste de tickets avec pagination
        """
        query = db.query(Ticket)
        
        if status:
            query = query.filter(Ticket.status == status)
        
        return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

# Instance globale
ticket_service = TicketService()