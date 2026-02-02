# ============================================================================
# FICHIER : backend/app/services/glpi_sync_service.py
# DESCRIPTION : Synchronisation bidirectionnelle GLPI ↔ Notre DB
# ============================================================================

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.models.ticket import Ticket
from app.models.user import User
from app.integrations.glpi_client import get_glpi_client, GLPIClientError
from app.integrations.glpi_mapping import GLPIMapping
from app.core.logger import structured_logger


class GLPISyncService:
    """
    Service de synchronisation bidirectionnelle avec GLPI
    
    Fonctionnalités:
    1. Pull: GLPI → Notre DB (récupérer mises à jour)
    2. Push: Notre DB → GLPI (envoyer modifications)
    3. Sync complète: Synchroniser tous les tickets
    """
    
    def __init__(self):
        self.glpi_client = get_glpi_client()
    
    # ========================================================================
    # PULL: GLPI → Notre DB
    # ========================================================================
    
    def sync_ticket_from_glpi(
        self,
        db: Session,
        glpi_ticket_id: int
    ) -> Optional[Ticket]:
        """
        Synchronise un ticket depuis GLPI vers notre DB
        
        Args:
            db: Session DB
            glpi_ticket_id: ID du ticket dans GLPI
        
        Returns:
            Ticket mis à jour ou None
        """
        try:
            # Récupérer le ticket depuis GLPI
            glpi_ticket = self.glpi_client.get_ticket(glpi_ticket_id)
            
            # Trouver le ticket dans notre DB
            ticket = db.query(Ticket).filter(
                Ticket.glpi_ticket_id == glpi_ticket_id
            ).first()
            
            if not ticket:
                structured_logger.log_error(
                    "GLPI_SYNC_TICKET_NOT_FOUND",
                    f"Ticket GLPI {glpi_ticket_id} non trouvé en DB"
                )
                return None
            
            # Mettre à jour les champs
            updates_made = False
            
            # Statut
            new_status = GLPIMapping.get_our_status(glpi_ticket.get("status", 1))
            if ticket.status != new_status:
                ticket.status = new_status
                ticket.glpi_status = glpi_ticket.get("status")
                updates_made = True
            
            # Priorité
            new_priority = GLPIMapping.get_our_priority(glpi_ticket.get("priority", 3))
            if ticket.priority != new_priority:
                ticket.priority = new_priority
                updates_made = True
            
            # Date de résolution
            if glpi_ticket.get("solvedate") and not ticket.resolved_at:
                ticket.resolved_at = datetime.fromisoformat(
                    glpi_ticket["solvedate"].replace("Z", "+00:00")
                )
                updates_made = True
            
            # Date de clôture
            if glpi_ticket.get("closedate") and not ticket.closed_at:
                ticket.closed_at = datetime.fromisoformat(
                    glpi_ticket["closedate"].replace("Z", "+00:00")
                )
                updates_made = True
            
            if updates_made:
                ticket.glpi_last_update = datetime.now()
                db.commit()
                db.refresh(ticket)
                
                structured_logger.log_error(
                    "GLPI_SYNC_UPDATED",
                    f"Ticket {ticket.ticket_number} synchronisé depuis GLPI"
                )
            
            return ticket
            
        except GLPIClientError as e:
            structured_logger.log_error("GLPI_SYNC_ERROR", str(e))
            return None
    
    def sync_all_tickets_from_glpi(
        self,
        db: Session,
        since: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Synchronise tous les tickets depuis GLPI
        
        Args:
            db: Session DB
            since: Synchroniser seulement les tickets modifiés depuis cette date
        
        Returns:
            Statistiques de synchronisation
        """
        stats = {
            "total": 0,
            "updated": 0,
            "errors": 0
        }
        
        # Récupérer tous nos tickets synchronisés avec GLPI
        query = db.query(Ticket).filter(
            Ticket.synced_to_glpi == True,
            Ticket.glpi_ticket_id.isnot(None)
        )
        print(f"Tickets à synchroniser depuis GLPI: {query.count()}")
        if since:
            query = query.filter(Ticket.glpi_last_update < since)
        
        tickets = query.all()
        stats["total"] = len(tickets)
        
        structured_logger.log_error(
            "GLPI_SYNC_START",
            f"Démarrage sync de {stats['total']} tickets depuis GLPI"
        )
        
        for ticket in tickets:
            try:
                result = self.sync_ticket_from_glpi(db, ticket.glpi_ticket_id)
                if result:
                    stats["updated"] += 1
            except Exception as e:
                stats["errors"] += 1
                structured_logger.log_error(
                    "GLPI_SYNC_TICKET_ERROR",
                    f"Ticket {ticket.ticket_number}: {str(e)}"
                )
        
        structured_logger.log_error(
            "GLPI_SYNC_COMPLETE",
            f"Sync terminée: {stats['updated']}/{stats['total']} mis à jour, {stats['errors']} erreurs"
        )
        
        return stats
    
    # ========================================================================
    # PUSH: Notre DB → GLPI
    # ========================================================================
    
    def push_ticket_to_glpi(
        self,
        db: Session,
        ticket_id: int,
        force: bool = False
    ) -> bool:
        """
        Pousse les modifications d'un ticket vers GLPI
        
        Args:
            db: Session DB
            ticket_id: ID du ticket dans notre DB
            force: Forcer la synchronisation même si déjà sync
        
        Returns:
            True si succès
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            return False
        
        if not ticket.glpi_ticket_id and not force:
            # Ticket pas encore dans GLPI
            return False
        
        try:
            # Préparer les mises à jour
            updates = {}
            
            # Statut
            if ticket.status:
                updates["status"] = GLPIMapping.get_glpi_status(ticket.status)
            
            # Priorité
            if ticket.priority:
                updates["priority"] = GLPIMapping.get_glpi_priority(ticket.priority)
            
            # Titre
            if ticket.title:
                updates["name"] = ticket.title
            
            # Description (attention: peut écraser)
            # updates["content"] = ticket.description  # Décommentez si nécessaire
            
            if not updates:
                return True  # Rien à mettre à jour
            
            # Envoyer à GLPI
            self.glpi_client.update_ticket(
                ticket_id=ticket.glpi_ticket_id,
                updates=updates
            )
            
            ticket.glpi_sync_at = datetime.now()
            db.commit()
            
            structured_logger.log_error(
                "GLPI_PUSH_SUCCESS",
                f"Ticket {ticket.ticket_number} poussé vers GLPI"
            )
            
            return True
            
        except GLPIClientError as e:
            structured_logger.log_error("GLPI_PUSH_ERROR", str(e))
            return False
    
    # ========================================================================
    # SYNCHRONISATION COMPLÈTE
    # ========================================================================
    
    def full_sync(
        self,
        db: Session,
        direction: str = "both"  # "pull", "push", "both"
    ) -> Dict[str, any]:
        """
        Synchronisation complète bidirectionnelle
        
        Args:
            db: Session DB
            direction: Direction de la sync
        
        Returns:
            Statistiques complètes
        """
        stats = {
            "pull": None,
            "push": None,
            "started_at": datetime.now().isoformat()
        }
        
        # Pull: GLPI → Notre DB
        if direction in ["pull", "both"]:
            structured_logger.log_error("GLPI_FULL_SYNC", "Démarrage PULL (GLPI → DB)")
            stats["pull"] = self.sync_all_tickets_from_glpi(db)
        
        # Push: Notre DB → GLPI
        if direction in ["push", "both"]:
            structured_logger.log_error("GLPI_FULL_SYNC", "Démarrage PUSH (DB → GLPI)")
            
            push_stats = {"total": 0, "updated": 0, "errors": 0}
            
            # Récupérer tickets modifiés récemment (pas sync depuis 1h)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            tickets = db.query(Ticket).filter(
                Ticket.synced_to_glpi == True,
                Ticket.glpi_ticket_id.isnot(None),
                Ticket.updated_at > one_hour_ago
            ).all()
            
            push_stats["total"] = len(tickets)
            
            for ticket in tickets:
                try:
                    if self.push_ticket_to_glpi(db, ticket.id):
                        push_stats["updated"] += 1
                except Exception as e:
                    push_stats["errors"] += 1
            
            stats["push"] = push_stats
        
        stats["completed_at"] = datetime.now().isoformat()
        
        return stats


# Instance globale
glpi_sync_service = GLPISyncService()