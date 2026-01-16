# ============================================================================
# FICHIER : backend/app/schemas/ticket.py
# DESCRIPTION : Schémas Pydantic pour validation des tickets
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TicketCreateFromMessage(BaseModel):
    """
    Schéma pour créer un ticket depuis un message utilisateur
    """
    message: str = Field(..., min_length=10, description="Message de l'utilisateur")
    user_email: Optional[str] = Field(None, description="Email de l'utilisateur (optionnel)")

class TicketAIAnalysis(BaseModel):
    """
    Résultat de l'analyse IA
    """
    suggested_category_id: int
    suggested_category_name: str
    confidence_score: float
    extracted_title: str
    extracted_symptoms: List[str]
    suggested_priority: str

class TicketResponse(BaseModel):
    """
    Réponse complète après création de ticket
    """
    id: int
    ticket_number: str
    title: str
    description: Optional[str]
    user_message: str
    status: str
    priority: str
    category_id: int
    category_name: str
    created_at: datetime
    ai_analysis: Optional[TicketAIAnalysis]
    
    class Config:
        from_attributes = True

class TicketList(BaseModel):
    """
    Liste de tickets
    """
    id: int
    ticket_number: str
    title: str
    status: str
    priority: str
    category_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True