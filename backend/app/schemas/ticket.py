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
=======
# ============================================================================
# FICHIER : backend/app/schemas/ticket.py
# DESCRIPTION : Schémas Pydantic pour validation des tickets
# ============================================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    user_message: str
    category_id: Optional[int] = None
    priority: str = "medium"


class TicketCreate(TicketBase):
    user_email: Optional[str] = None


class TicketRead(TicketBase):
    id: int
    ticket_number: str
    status: str
    glpi_ticket_id: Optional[int]
    synced_to_glpi: bool
    ready_for_L1: bool
    created_at: datetime

    class Config:
        from_attributes = True
