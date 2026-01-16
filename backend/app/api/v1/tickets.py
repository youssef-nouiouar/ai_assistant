# ============================================================================
# FICHIER : backend/app/api/v1/tickets.py
# DESCRIPTION : Routes API pour les tickets
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_database
from app.schemas.ticket import TicketCreateFromMessage, TicketResponse, TicketList
from app.services.ticket_service import ticket_service
from app.models.category import Category

router = APIRouter()

@router.post("/create-from-message", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_from_message(
    data: TicketCreateFromMessage,
    db: Session = Depends(get_database)
):
    """
    Créer un ticket automatiquement depuis un message utilisateur 
    
    **Composant 1 : Intelligent Ticket Analysis**
    
    Cette route:
    1. Analyse le message avec l'IA (GPT-4 ou Ollama)
    2. Extrait : catégorie, priorité, symptômes, titre
    3. Crée le ticket dans la base de données
    4. Retourne le ticket créé avec l'analyse IA
    """
    try:
        result = await ticket_service.create_ticket_from_message(
            db=db,
            message=data.message,
            user_email=data.user_email
        )
        
        ticket = result["ticket"]
        category_name = result["category_name"]
        ai_analysis = result["ai_analysis"]
        
        # Construire la réponse
        category = db.query(Category).filter(Category.id == ticket.category_id).first()
        
        return TicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            title=ticket.title,
            description=ticket.description,
            user_message=ticket.user_message,
            status=ticket.status,
            priority=ticket.priority,
            category_id=ticket.category_id,
            category_name=category_name,
            created_at=ticket.created_at,
            ai_analysis={
                "suggested_category_id": ai_analysis["category_id"],
                "suggested_category_name": category_name,
                "confidence_score": ai_analysis["confidence_score"],
                "extracted_title": ai_analysis["title"],
                "extracted_symptoms": ai_analysis["symptoms"],
                "suggested_priority": ai_analysis["priority"]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du ticket: {str(e)}"
        )

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_database)
):
    """
    Récupérer un ticket par son ID
    """
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} non trouvé"
        )
    
    category = db.query(Category).filter(Category.id == ticket.category_id).first()
    
    return TicketResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        user_message=ticket.user_message,
        status=ticket.status,
        priority=ticket.priority,
        category_id=ticket.category_id,
        category_name=category.name if category else "Unknown",
        created_at=ticket.created_at,
        ai_analysis=None
    )

@router.get("/", response_model=List[TicketList])
def list_tickets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_database)
):
    """
    Lister les tickets avec pagination
    """
    tickets = ticket_service.get_tickets(db, skip=skip, limit=limit, status=status)
    
    result = []
    for ticket in tickets:
        category = db.query(Category).filter(Category.id == ticket.category_id).first()
        result.append(TicketList(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            title=ticket.title,
            status=ticket.status,
            priority=ticket.priority,
            category_name=category.name if category else "Unknown",
            created_at=ticket.created_at
        ))
    
    return result