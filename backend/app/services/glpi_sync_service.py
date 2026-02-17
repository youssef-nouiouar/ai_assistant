# ============================================================================
# FICHIER : backend/app/services/glpi_sync_service.py
# DESCRIPTION : Synchronisation GLPI -> Notre DB via webhook
# ============================================================================

from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime

from app.models.ticket import Ticket
from app.integrations.glpi_client import get_glpi_client, GLPIClientError
from app.integrations.glpi_mapping import GLPIMapping
from app.core.logger import structured_logger


class GLPISyncService:
    """
    Service de synchronisation avec GLPI.

    Utilise les données du webhook directement (pas de call API supplémentaire).
    Push vers GLPI lors de la création/modification de tickets côté backend.
    """

    def __init__(self):
        self._client = None

    @property
    def glpi_client(self):
        """Lazy init to avoid import-time errors."""
        if self._client is None:
            self._client = get_glpi_client()
        return self._client

    # ========================================================================
    # PULL: Sync from webhook payload (NO extra API call)
    # ========================================================================

    def sync_from_webhook_payload(
        self,
        db: Session,
        glpi_ticket_id: int,
        payload: Dict,
    ) -> Optional[Ticket]:
        """
        Synchronise un ticket en utilisant les données du webhook directement.

        Args:
            db: Session DB
            glpi_ticket_id: ID du ticket dans GLPI
            payload: Données reçues du webhook (déjà parsées)
        """
        ticket = db.query(Ticket).filter(
            Ticket.glpi_ticket_id == glpi_ticket_id
        ).first()

        if not ticket:
            structured_logger.log_info(
                "GLPI_SYNC_NOT_FOUND",
                f"Ticket GLPI {glpi_ticket_id} not in local DB"
            )
            return None

        changes = []

        # Status
        new_status = self._extract_status_from_payload(payload)
        if new_status and ticket.status != new_status:
            changes.append(f"status: {ticket.status} -> {new_status}")
            ticket.status = new_status

        # Priority
        new_priority = self._extract_priority_from_payload(payload)
        if new_priority and ticket.priority != new_priority:
            changes.append(f"priority: {ticket.priority} -> {new_priority}")
            ticket.priority = new_priority

        # Title
        new_title = payload.get("title", "")
        if new_title and new_title != ticket.title:
            changes.append(f"title updated")
            ticket.title = new_title[:200]

        # Closing date
        close_date = payload.get("closing_date") or payload.get("closedate")
        if close_date and close_date.strip() and not ticket.closed_at:
            try:
                ticket.closed_at = datetime.fromisoformat(
                    close_date.replace("Z", "+00:00")
                )
                changes.append("closed_at set")
            except (ValueError, AttributeError):
                pass

        # Update sync timestamp
        ticket.glpi_last_update = datetime.now()

        if changes:
            db.commit()
            db.refresh(ticket)
            structured_logger.log_info(
                "GLPI_SYNC_WEBHOOK",
                f"Ticket {ticket.ticket_number} synced from webhook: {', '.join(changes)}"
            )
        else:
            db.commit()

        return ticket

    # ========================================================================
    # PUSH: Notre DB -> GLPI
    # ========================================================================

    def push_ticket_to_glpi(
        self,
        db: Session,
        ticket_id: int,
    ) -> bool:
        """Pousse les modifications d'un ticket vers GLPI."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket or not ticket.glpi_ticket_id:
            return False

        # Conflict check: GLPI modified more recently -> skip push
        if ticket.glpi_last_update and ticket.updated_at:
            if ticket.glpi_last_update > ticket.updated_at:
                return True

        updates = {}

        if ticket.status:
            updates["status"] = GLPIMapping.get_glpi_status(ticket.status)
        if ticket.priority:
            updates["priority"] = GLPIMapping.get_glpi_priority(ticket.priority)
        if ticket.title:
            updates["name"] = ticket.title

        if not updates:
            return True

        try:
            self.glpi_client.update_ticket(
                ticket_id=ticket.glpi_ticket_id,
                updates=updates,
            )
            ticket.glpi_sync_at = datetime.now()
            db.commit()
            structured_logger.log_info(
                "GLPI_SYNC_PUSHED",
                f"Ticket {ticket.ticket_number} pushed to GLPI: {list(updates.keys())}"
            )
            return True
        except GLPIClientError as e:
            structured_logger.log_error("GLPI_SYNC_PUSH_ERROR", str(e))
            return False

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _extract_status_from_payload(self, payload: Dict) -> Optional[str]:
        """Extract status from webhook data (handles both numeric and label)."""
        raw = payload.get("status")
        if raw is None:
            event = payload.get("event", "")
            if "solved" in event:
                return "resolved"
            if "closed" in event:
                return "closed"
            return None

        # Numeric
        try:
            return GLPIMapping.get_our_status(int(raw))
        except (ValueError, TypeError):
            pass

        # String label (e.g. "Pending", "Processing (assigned)")
        glpi_int = self._status_label_to_int(str(raw))
        if glpi_int:
            return GLPIMapping.get_our_status(glpi_int)

        return None

    def _extract_priority_from_payload(self, payload: Dict) -> Optional[str]:
        """Extract priority from webhook data (handles both numeric and label)."""
        raw = payload.get("priority")
        if raw is None:
            return None

        # Numeric
        try:
            return GLPIMapping.get_our_priority(int(raw))
        except (ValueError, TypeError):
            pass

        # String label
        label_map = {
            "very low": "very_low",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "very high": "critical",
            "major": "major",
        }
        return label_map.get(str(raw).lower().strip())

    @staticmethod
    def _status_label_to_int(label: str) -> Optional[int]:
        """Convert GLPI status label to numeric ID."""
        label_map = {
            "new": 1,
            "nouveau": 1,
            "processing (assigned)": 2,
            "assigned": 2,
            "en cours (attribué)": 2,
            "processing (planned)": 3,
            "planned": 3,
            "en cours (planifié)": 3,
            "pending": 4,
            "en attente": 4,
            "solved": 5,
            "résolu": 5,
            "closed": 6,
            "clos": 6,
        }
        return label_map.get(label.lower().strip())


# Instance globale
glpi_sync_service = GLPISyncService()
