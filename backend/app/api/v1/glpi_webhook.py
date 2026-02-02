# ============================================================================
# FICHIER : backend/app/api/v1/glpi_webhook.py
# DESCRIPTION : Endpoint webhook pour notifications GLPI
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib

from app.api.deps import get_database
from app.services.glpi_sync_service import glpi_sync_service
from app.core.config import settings
from app.core.logger import structured_logger


router = APIRouter()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Vérifie la signature du webhook GLPI
    
    Args:
        payload: Corps de la requête
        signature: Signature reçue
        secret: Secret partagé
    
    Returns:
        True si signature valide
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/ticket-updated")
async def glpi_ticket_updated_webhook(
    request: Request,
    db: Session = Depends(get_database),
    x_glpi_signature: Optional[str] = Header(None)
):
    """
    Webhook appelé par GLPI quand un ticket est mis à jour
    
    Configuration GLPI nécessaire:
    1. Installer le plugin "Webhook" dans GLPI
    2. Configurer l'URL: http://votre-backend/api/v1/glpi/webhook/ticket-updated
    3. Événements: Ticket Updated, Ticket Solved, Ticket Closed
    4. Secret: Définir dans .env (GLPI_WEBHOOK_SECRET)
    
    Payload attendu:
    {
        "event": "ticket.updated",
        "ticket_id": 123,
        "changes": {
            "status": {"old": 1, "new": 2},
            "priority": {"old": 3, "new": 4}
        },
        "timestamp": "2025-01-30T10:00:00Z"
    }
    """
    
    # Récupérer le payload
    payload = await request.body()
    data = await request.json()
    
    # Vérifier la signature (si activée)
    if settings.GLPI_WEBHOOK_SECRET and x_glpi_signature:
        if not verify_webhook_signature(
            payload,
            x_glpi_signature,
            settings.GLPI_WEBHOOK_SECRET
        ):
            structured_logger.log_error(
                "GLPI_WEBHOOK_INVALID_SIGNATURE",
                "Signature invalide"
            )
            raise HTTPException(status_code=401, detail="Signature invalide")
    
    # Extraire les données
    event = data.get("event")
    
    ticket_id = data.get("ticket_id")
    changes = data.get("changes", {})
    
    structured_logger.log_error(
        "GLPI_WEBHOOK_RECEIVED",
        f"Event: {event}, Ticket: {ticket_id}"
    )
    
    # Gérer l'événement
    if event == "ticket.updated":
        print("GLPI Ticket Updated Webhook reçu pour le ticket", ticket_id)
        # Synchroniser le ticket
        ticket = glpi_sync_service.sync_ticket_from_glpi(db, ticket_id)
        
        if ticket:
            return {
                "status": "success",
                "message": f"Ticket {ticket.ticket_number} synchronisé",
                "ticket_id": ticket.id,
                "changes_applied": len(changes)
            }
        else:
            return {
                "status": "warning",
                "message": "Ticket non trouvé en DB locale",
                "ticket_id": ticket_id
            }
    
    elif event == "ticket.solved":
        print("GLPI Ticket Solved Webhook reçu pour le ticket", ticket_id)
        # Marquer comme résolu
        ticket = glpi_sync_service.sync_ticket_from_glpi(db, ticket_id)
        
        if ticket:
            structured_logger.log_error(
                "GLPI_TICKET_SOLVED",
                f"Ticket {ticket.ticket_number} résolu dans GLPI"
            )
            
            return {
                "status": "success",
                "message": f"Ticket {ticket.ticket_number} marqué résolu"
            }
    
    elif event == "ticket.closed":
        # Marquer comme fermé
        ticket = glpi_sync_service.sync_ticket_from_glpi(db, ticket_id)
        
        if ticket:
            structured_logger.log_error(
                "GLPI_TICKET_CLOSED",
                f"Ticket {ticket.ticket_number} fermé dans GLPI"
            )
            
            return {
                "status": "success",
                "message": f"Ticket {ticket.ticket_number} fermé"
            }
    
    return {"status": "ignored", "event": event}


@router.post("/followup-added")
async def glpi_followup_added_webhook(
    request: Request,
    db: Session = Depends(get_database),
    x_glpi_signature: Optional[str] = Header(None)
):
    """
    Webhook appelé quand un suivi est ajouté dans GLPI
    
    Payload:
    {
        "event": "followup.added",
        "ticket_id": 123,
        "followup_id": 456,
        "content": "Intervention effectuée...",
        "is_private": false,
        "user_id": 789
    }
    """
    
    payload = await request.body()
    data = await request.json()
    
    # Vérifier signature
    if settings.GLPI_WEBHOOK_SECRET and x_glpi_signature:
        if not verify_webhook_signature(
            payload,
            x_glpi_signature,
            settings.GLPI_WEBHOOK_SECRET
        ):
            raise HTTPException(status_code=401, detail="Signature invalide")
    
    ticket_id = data.get("ticket_id")
    content = data.get("content", "")
    
    structured_logger.log_error(
        "GLPI_FOLLOWUP_ADDED",
        f"Suivi ajouté au ticket GLPI {ticket_id}"
    )
    
    # Optionnel: Stocker le suivi en DB locale
    # ou notifier l'utilisateur via websocket
    
    return {
        "status": "success",
        "message": "Suivi enregistré"
    }