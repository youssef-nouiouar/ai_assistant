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
    message: str = Field(..., min_length=1, description="Message de l'utilisateur")
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
    selected_choice_id: Optional[str] = Field(None, description="ID du choix guidé sélectionné")


class TopicShiftChoiceInput(BaseModel):
    """Choix de l'utilisateur suite à un changement de sujet détecté"""
    session_id: str = Field(..., description="ID de la session topic_shift")
    choice: str = Field(
        ...,
        description="Choix: 'keep_new', 'keep_old', ou 'both_problems'"
    )

    @validator('choice')
    def validate_choice(cls, v):
        valid_choices = ["keep_new", "keep_old", "both_problems"]
        if v not in valid_choices:
            raise ValueError(f"Choix invalide. Options: {', '.join(valid_choices)}")
        return v


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


class GuidedChoiceSchema(BaseModel):
    """Phase 2 - Choix cliquable proposé à l'utilisateur"""
    id: str
    label: str
    icon: str = ""


class SuggestionMetadata(BaseModel):
    """Métadonnées des suggestions intelligentes"""
    reasoning: Optional[str] = None  # Raisonnement transparent pour l'utilisateur
    should_regenerate: bool = False  # Indique si les suggestions ont été régénérées
    regeneration_reason: Optional[str] = None  # Raison de la régénération
    relevance_score: float = 100.0  # Score de pertinence (0-100)


class AnalysisResponse(BaseModel):
    """
    Réponse après analyse (flexible)

    Phase 2 : Ajout de guided_choices et show_examples
    Phase 3 : Ajout de suggestion_metadata pour raisonnement transparent
    """
    session_id: Optional[str] = None  # None pour greeting/non_it
    type: str = "smart_summary"
    action: str  # auto_validate, confirm_summary, ask_clarification, too_vague, greeting, non_it
    message: str
    summary: Optional[SmartSummary] = None  # Peut être None si too_vague
    clarification_questions: Optional[List[str]] = None  # Questions ciblées
    clarification_attempts: int = 0  # Nombre de tentatives
    guided_choices: Optional[List[GuidedChoiceSchema]] = None  # Phase 2 : Choix cliquables
    suggestion_metadata: Optional[SuggestionMetadata] = None  # Phase 3 : Raisonnement transparent
    show_examples: Optional[bool] = None  # Phase 1 : Afficher exemples
    expires_at: Optional[str] = None  # None pour greeting/non_it


class TicketCreatedResponse(BaseModel):
    """Réponse après création ticket (avec GLPI)"""
    type: str = "ticket_created"
    ticket_id: int
    ticket_number: str
    glpi_ticket_id: Optional[int] = None
    title: str
    status: str
    priority: str
    category_name: str
    created_at: str
    ready_for_L1: bool
    synced_to_glpi: bool = False
    escalated_to_human: Optional[bool] = None  # Phase 1 : escalade humaine
    message: str


class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    type: str = "error"
    message: str
    error_code: Optional[str] = None