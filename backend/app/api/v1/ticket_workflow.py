# ============================================================================
# FICHIER : backend/app/api/v1/ticket_workflow.py
# DESCRIPTION : Routes API (Production Grade)
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api.deps import get_database
from app.schemas.ticket_workflow import (
    MessageInput,
    AutoValidateInput,
    ConfirmSummaryInput,
    ClarificationInput,
    RestartFromInput,
    AnalysisResponse,
    TicketCreatedResponse
)
import time
from app.services.ticket_workflow import ticket_workflow
from app.core.exceptions import (
    SessionNotFoundError,
    SessionAlreadyConvertedError,
    InvalidUserResponseError,
    AIAnalysisError
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze")
@limiter.limit("15/minute")
async def analyze_message(
    request: Request,
    data: MessageInput,
    db: Session = Depends(get_database)
):
    """
    **COMPOSANT 0 - Analyse du message**

    Phase 2 :
    - ✅ Supporte greeting/non_it (sans session)
    - ✅ Supporte ticket_created (max attempts)
    - ✅ Supporte guided_choices (choix cliquables)
    - ✅ Logs structurés
    """
    try:
        started_at = time.time()
        result = await ticket_workflow.analyze_message(
            db=db,
            message=data.message,
            user_email=data.user_email
        )
        ended_at = time.time()
        print("\nAnalysis Result:", result, "Time taken:", ended_at - started_at)

        # Phase 2: Retourner le bon type de réponse
        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except AIAnalysisError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/auto-validate", response_model=TicketCreatedResponse)
async def auto_validate_and_create(
    data: AutoValidateInput,
    db: Session = Depends(get_database)
):
    """
    **ACTION : AUTO_VALIDATE**
    
    Production Grade :
    - ✅ Récupère données depuis session (sécurité)
    - ✅ Validation intelligente de l'intention
    - ✅ Idempotence garantie
    """
    try:
        result = await ticket_workflow.handle_auto_validate(
            db=db,
            session_id=data.session_id,
            user_response=data.user_response
        )
        
        return TicketCreatedResponse(**result)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionAlreadyConvertedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidUserResponseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm-summary", response_model=TicketCreatedResponse)
async def confirm_or_modify_summary(
    data: ConfirmSummaryInput,
    db: Session = Depends(get_database)
):
    """
    **ACTION : CONFIRM_SUMMARY**
    
    Production Grade :
    - ✅ Modifications appliquées côté serveur
    - ✅ Idempotence garantie
    """
    try:
        result = await ticket_workflow.handle_confirm_summary(
            db=db,
            session_id=data.session_id,
            user_action=data.user_action,
            modifications=data.modifications
        )
        
        return TicketCreatedResponse(**result)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionAlreadyConvertedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/clarify")
@limiter.limit("20/minute")
async def handle_clarification(
    request: Request,
    data: ClarificationInput,
    db: Session = Depends(get_database)
):
    """
    **ACTION : ASK_CLARIFICATION**

    Phase 2 :
    - ✅ Invalide l'ancienne session
    - ✅ Crée une nouvelle session
    - ✅ Supporte ticket_created si max attempts atteint
    - ✅ Supporte guided_choices
    """
    try:
        result = await ticket_workflow.handle_clarification(
            db=db,
            session_id=data.session_id,
            clarification_response=data.clarification_response,
            selected_choice_id=data.selected_choice_id
        )

        # Phase 2: Retourner le bon type de réponse
        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidUserResponseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_database)
):
    """
    Récupère les données d'une session existante (restauration après page refresh).
    """
    try:
        session = ticket_workflow._get_valid_session(db, session_id)
        return {
            "session_id": session.id,
            "action": session.action_type,
            "summary": session.ai_summary,
            "clarification_attempts": session.clarification_attempts,
            "expires_at": session.expires_at.isoformat()
        }
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionAlreadyConvertedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/restart-from")
async def restart_from(
    data: RestartFromInput,
    db: Session = Depends(get_database)
):
    """
    Invalide la session courante et relance l'analyse depuis un message modifié.
    """
    try:
        result = await ticket_workflow.handle_restart_from(
            db=db,
            session_id=data.session_id,
            edited_message=data.edited_message,
            user_email=data.user_email
        )

        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIAnalysisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


