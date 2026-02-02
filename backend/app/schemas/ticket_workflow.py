# ============================================================================
# FICHIER : backend/app/schemas/ticket_workflow.py
# DESCRIPTION : Schémas Pydantic (Version Flexible)
# ============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


# ========================================================================
# INPUT SCHEMAS
# ========================================================================

class MessageInput(BaseModel):
    """Message utilisateur initial"""
    message: str = Field(..., min_length=5, description="Message de l'utilisateur")
    user_email: Optional[str] = Field(None, description="Email utilisateur")


class AutoValidateInput(BaseModel):
    """Réponse pour auto-validation"""
    session_id: str = Field(..., description="ID de la session")
    user_response: str = Field(..., description="Réponse utilisateur")


class ConfirmSummaryInput(BaseModel):
    """Confirmation ou modification RESTREINTE"""
    session_id: str = Field(..., description="ID de la session")
    user_action: str = Field(..., description="'confirm' ou 'modify'")
    modifications: Optional[Dict[str, Any]] = Field(
        None, 
        description="Modifications autorisées : title, symptoms uniquement"
    )
    
    @validator('modifications')
    def validate_modifications(cls, v):
        """Valide que seuls les champs autorisés sont modifiés"""
        if v:
            forbidden_fields = ["priority", "category_id", "confidence", "category"]
            for field in forbidden_fields:
                if field in v:
                    raise ValueError(
                        f"Modification du champ '{field}' non autorisée. "
                        "Seuls 'title' et 'symptoms' peuvent être modifiés."
                    )
        return v


class ClarificationInput(BaseModel):
    """Réponse à clarification"""
    session_id: str = Field(..., description="ID de la session")
    clarification_response: str = Field(..., description="Réponse détaillée")


# ========================================================================
# OUTPUT SCHEMAS (Flexibles pour gérer None)
# ========================================================================

class CategorySummary(BaseModel):
    """Catégorie (peut être None si pas assez d'infos)"""
    id: Optional[int] = None
    name: Optional[str] = None
    confidence: Optional[float] = None


class SmartSummary(BaseModel):
    """
    Résumé intelligent (flexible)
    
    IMPORTANT : category peut être None si message trop vague
    """
    category: Optional[CategorySummary] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    symptoms: List[str] = []
    extracted_info: Dict[str, Any] = {}
    missing_info: List[str] = []  # NOUVEAU : Liste des infos manquantes


class AnalysisResponse(BaseModel):
    """
    Réponse après analyse (flexible)
    """
    session_id: str
    type: str = "smart_summary"
    action: str  # auto_validate, confirm_summary, ask_clarification, too_vague
    message: str
    summary: Optional[SmartSummary] = None  # Peut être None si too_vague
    clarification_questions: Optional[List[str]] = None  # Questions ciblées
    clarification_attempts: int = 0  # Nombre de tentatives
    expires_at: str


class TicketCreatedResponse(BaseModel):
    """Réponse après création ticket (avec GLPI)"""
    type: str = "ticket_created"
    ticket_id: int
    ticket_number: str
    glpi_ticket_id: Optional[int] = None  # NOUVEAU
    title: str
    status: str
    priority: str
    category_name: str
    created_at: str
    ready_for_L1: bool
    synced_to_glpi: bool = False  # NOUVEAU
    message: str


class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    type: str = "error"
    message: str
    error_code: Optional[str] = None