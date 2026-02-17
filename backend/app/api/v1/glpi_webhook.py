# ============================================================================
# FICHIER : backend/app/api/v1/glpi_webhook.py
# DESCRIPTION : Endpoint webhook pour notifications GLPI
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import hmac
import hashlib
import json
import re
import base64

from app.api.deps import get_database
from app.services.glpi_sync_service import glpi_sync_service
from app.core.config import settings
from app.core.logger import structured_logger


router = APIRouter()


def verify_webhook_auth(request: Request) -> bool:
    """
    Vérifie l'authentification du webhook GLPI.

    GLPI envoie le secret via 'Authorization: Basic glpi:<secret>'
    """
    if not settings.GLPI_WEBHOOK_SECRET:
        return True  # Pas de secret configuré = pas de vérification

    auth_header = request.headers.get("authorization", "")

    # Format: "Basic glpi:<secret>"
    if auth_header.startswith("Basic "):
        credentials = auth_header[6:]  # Enlever "Basic "

        # GLPI envoie en clair "glpi:<secret>" (pas encodé en base64)
        if ":" in credentials:
            _, secret = credentials.split(":", 1)
            return hmac.compare_digest(secret, settings.GLPI_WEBHOOK_SECRET)

        # Essayer décodage base64 au cas où
        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
            if ":" in decoded:
                _, secret = decoded.split(":", 1)
                return hmac.compare_digest(secret, settings.GLPI_WEBHOOK_SECRET)
        except Exception:
            pass

    # Fallback: X-GLPI-Signature header (plugin webhooks)
    signature = request.headers.get("x-glpi-signature", "")
    if signature:
        payload = request.state.raw_payload if hasattr(request.state, "raw_payload") else b""
        expected = hmac.new(
            settings.GLPI_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    return False


def parse_glpi_text_body(text: str) -> Dict[str, Any]:
    """
    Parse le body texte d'une notification GLPI.

    GLPI notification format exemple :
    "Title : Mon ticket\n\nClosing Date : \n\nInvitation..."

    Extrait les champs clé-valeur.
    """
    data = {"_raw_text": text}

    # Parser les lignes "Key : Value"
    for line in text.split("\n"):
        line = line.strip()
        if " : " in line:
            key, value = line.split(" : ", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            if value:  # Ignorer les valeurs vides
                data[key] = value

    return data


async def parse_glpi_payload(request: Request) -> Dict[str, Any]:
    """
    Parse le payload GLPI de manière robuste.

    GLPI peut envoyer :
    - JSON valide (si template configuré correctement)
    - Texte de notification (format "Key : Value" par défaut)
    - Corps vide
    """
    payload = await request.body()

    # Log raw payload pour debug
    content_type = request.headers.get("content-type", "unknown")
    print(f"[GLPI WEBHOOK] Content-Type: {content_type}")
    print(f"[GLPI WEBHOOK] Raw body ({len(payload)} bytes): {payload[:500]}")
    print(f"[GLPI WEBHOOK] Query params: {dict(request.query_params)}")

    if not payload or len(payload) == 0:
        print("[GLPI WEBHOOK] Empty body received")
        return {}

    text = payload.decode("utf-8", errors="replace").strip()

    # 1. Essayer JSON direct
    try:
        data = json.loads(text)
        print(f"[GLPI WEBHOOK] Parsed JSON OK: {json.dumps(data, indent=2, default=str)[:1000]}")
        return data
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Essayer de réparer le JSON cassé de GLPI
    #    GLPI peut envoyer: {"ticket_id":0000097,"status":Pending,"priority":Medium}
    #    - Nombres avec zéros initiaux (0000097) -> les mettre en string
    #    - Valeurs non-quotées (Pending, Medium, Low) -> les quoter
    if text.startswith("{"):
        fixed = text
        # Quoter les valeurs non-quotées après ":"
        # Match :value qui n'est pas un string, nombre valide, null, true, false, objet, ou array
        fixed = re.sub(
            r':(\s*)([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 ]*?)(\s*[,}])',
            r':\1"\2"\3',
            fixed
        )
        # Corriger les nombres avec zéros initiaux: :0000097, -> :"0000097",
        fixed = re.sub(
            r':(\s*)(0\d+)(\s*[,}])',
            r':\1"\2"\3',
            fixed
        )
        try:
            data = json.loads(fixed)
            print(f"[GLPI WEBHOOK] Parsed FIXED JSON: {json.dumps(data, indent=2, default=str)[:1000]}")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[GLPI WEBHOOK] JSON repair failed: {e}")
            print(f"[GLPI WEBHOOK] Fixed text was: {fixed[:500]}")

    # 3. Fallback: body est du texte brut (notification GLPI par défaut)
    print(f"[GLPI WEBHOOK] Body is plain text, parsing as notification template...")
    data = parse_glpi_text_body(text)
    print(f"[GLPI WEBHOOK] Extracted from text: {data}")
    return data


def extract_ticket_id(data: Dict[str, Any]) -> Optional[int]:
    """
    Extrait le ticket_id depuis différents formats GLPI.

    GLPI peut envoyer l'ID sous différentes clés selon la version/plugin :
    - {"ticket_id": 123}
    - {"id": 123}
    - {"items_id": 123}
    - {"input": {"id": 123}}
    - {"ticket": {"id": 123}}
    """
    # Format direct
    for key in ["ticket_id", "id", "items_id"]:
        val = data.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                continue

    # Format imbriqué : {"input": {"id": 123}}
    if isinstance(data.get("input"), dict):
        val = data["input"].get("id") or data["input"].get("items_id")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

    # Format imbriqué : {"ticket": {"id": 123}}
    if isinstance(data.get("ticket"), dict):
        val = data["ticket"].get("id")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

    return None


def extract_event_type(data: Dict[str, Any]) -> str:
    """
    Détermine le type d'événement depuis le payload GLPI.
    """
    # Champ event explicite
    event = data.get("event", "")
    print(f"[GLPI WEBHOOK] Extracted event from payload: {event}")
    if event:
        return event

    # Détecter via le statut GLPI
    status = None
    if isinstance(data.get("input"), dict):
        status = data["input"].get("status")
    elif data.get("status"):
        status = data.get("status")
    print(f"[GLPI WEBHOOK] Extracted status for event type detection: {status}")
    if status is not None:
        status = int(status) if str(status).isdigit() else None
        if status == 5:
            return "ticket.solved"
        elif status == 6:
            return "ticket.closed"

    # Par défaut
    return "ticket.updated"


@router.post("/ticket-updated")
async def glpi_ticket_updated_webhook(
    request: Request,
    db: Session = Depends(get_database),
):
    """
    Webhook appelé par GLPI quand un ticket est mis à jour.

    Gère les formats de payload GLPI variés (JSON, vide, form data).
    """

    # Récupérer et parser le payload de manière robuste
    raw_payload = await request.body()

    # Rembobiner le body pour pouvoir le relire
    async def receive():
        return {"type": "http.request", "body": raw_payload}
    request._receive = receive

    data = await parse_glpi_payload(request)

    # Vérifier l'authentification (Authorization: Basic ou X-GLPI-Signature)
    request.state.raw_payload = raw_payload
    if settings.GLPI_WEBHOOK_SECRET:
        if not verify_webhook_auth(request):
            structured_logger.log_error(
                "GLPI_WEBHOOK_INVALID_AUTH",
                "Authentification invalide"
            )
            raise HTTPException(status_code=401, detail="Authentification invalide")

    # Extraire ticket_id et event type
    ticket_id = extract_ticket_id(data)
    event = extract_event_type(data)

    structured_logger.log_info(
        "GLPI_WEBHOOK_RECEIVED",
        f"Event: {event}, Ticket: {ticket_id}, Data keys: {list(data.keys())}"
    )

    print(f"[GLPI WEBHOOK] Event: {event}, Ticket ID: {ticket_id}")

    # Si pas de ticket_id, on log et on retourne OK (ne pas bloquer GLPI)
    if ticket_id is None:
        print("[GLPI WEBHOOK] No ticket_id found in payload - returning OK")
        print("[GLPI WEBHOOK] Full data received:", json.dumps(data, indent=2, default=str)[:2000])
        return {
            "status": "received",
            "message": "Webhook received but no ticket_id found in payload.",
            "data_keys": list(data.keys()),
            "hint": "Configure GLPI notification template to include ##ticket.id##"
        }

    # Synchroniser directement depuis le payload (PAS de call API supplémentaire)
    print(f"[GLPI WEBHOOK] Syncing ticket {ticket_id} from webhook payload (no extra API call)...")

    try:
        ticket = glpi_sync_service.sync_from_webhook_payload(db, ticket_id, data)
    except Exception as e:
        print(f"[GLPI WEBHOOK] Sync error: {str(e)}")
        structured_logger.log_error("GLPI_WEBHOOK_SYNC_ERROR", str(e))
        return {
            "status": "error",
            "message": f"Sync failed: {str(e)}",
            "ticket_id": ticket_id
        }

    if ticket:
        event_label = {
            "ticket.updated": "synchronisé",
            "ticket.solved": "marqué résolu",
            "ticket.closed": "fermé"
        }.get(event, "traité")

        structured_logger.log_error(
            "GLPI_WEBHOOK_SUCCESS",
            f"Ticket {ticket.ticket_number} {event_label} (GLPI ID: {ticket_id})"
        )

        return {
            "status": "success",
            "message": f"Ticket {ticket.ticket_number} {event_label}",
            "ticket_id": ticket.id,
            "glpi_ticket_id": ticket_id,
            "event": event
        }
    else:
        return {
            "status": "warning",
            "message": "Ticket non trouvé en DB locale (normal si créé directement dans GLPI)",
            "glpi_ticket_id": ticket_id,
            "event": event
        }