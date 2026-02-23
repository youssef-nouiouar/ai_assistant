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
from app.integrations.glpi_client import get_glpi_client
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
from app.services.input_guard import input_guard
from app.models.user import User
from app.core.exceptions import (
    SessionNotFoundError,
    SessionAlreadyConvertedError,
    InvalidUserResponseError,
    AIAnalysisError,
    InputGuardError,
)
from app.core.logger import structured_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


async def _verify_user_email(db: Session, user_email: str | None) -> str | None:
    """
    If a user_email is provided, verify it matches a record in the Users table.
    Returns the validated email or None.  Raises HTTP 403 if the email is
    not found — preventing impersonation of non-existent identities.

    Also ensures glpi_user_id is populated: if it is null, the user is created
    in GLPI and the local record is updated with the returned ID.
    """
    if not user_email:
        return None

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        structured_logger.log_error(
            "USER_EMAIL_INVALID",
            f"Rejected unknown user_email: {user_email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Adresse email inconnue : {user_email}. "
                   "Veuillez utiliser votre adresse email professionnelle."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte utilisateur est désactivé."
        )

    if user.glpi_user_id is None:
        structured_logger.log_info(
            "GLPI_USER_SYNC",
            f"glpi_user_id manquant pour {user_email} — création dans GLPI"
        )
        glpi_client = get_glpi_client()
        glpi_id = await glpi_client.create_user(
            email=user.email,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )
        if glpi_id:
            user.glpi_user_id = glpi_id
            db.commit()
            structured_logger.log_info(
                "GLPI_USER_SYNC_OK",
                f"glpi_user_id={glpi_id} enregistré pour {user_email}"
            )
        else:
            structured_logger.log_error(
                "GLPI_USER_SYNC_FAILED",
                f"Impossible de créer {user_email} dans GLPI"
            )

    return user_email


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
        clean_message = input_guard.validate(data.message, field="message")
        verified_email = await _verify_user_email(db, data.user_email)
        started_at = time.time()
        result = await ticket_workflow.analyze_message(
            db=db,
            message=clean_message,
            user_email=verified_email
        )
        ended_at = time.time()
        print("\nAnalysis Result:", result, "Time taken:", ended_at - started_at)

        # Phase 2: Retourner le bon type de réponse
        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except InputGuardError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        clean_response = input_guard.validate(
            data.clarification_response, field="clarification_response"
        )
        result = await ticket_workflow.handle_clarification(
            db=db,
            session_id=data.session_id,
            clarification_response=clean_response,
            selected_choice_id=data.selected_choice_id
        )

        # Phase 2: Retourner le bon type de réponse
        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except InputGuardError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        clean_edited = input_guard.validate(data.edited_message, field="edited_message")
        verified_email = await _verify_user_email(db, data.user_email)
        result = await ticket_workflow.handle_restart_from(
            db=db,
            session_id=data.session_id,
            edited_message=clean_edited,
            user_email=verified_email
        )

        if result.get("type") == "ticket_created":
            return TicketCreatedResponse(**result)

        return AnalysisResponse(**result)

    except InputGuardError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIAnalysisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


