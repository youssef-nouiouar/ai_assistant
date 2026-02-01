# ============================================================================
# FICHIER : backend/app/models/ticket.py
# DESCRIPTION : Modèle Ticket simplifié pour Composant 0
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    
    # ========================================================================
    # IDENTIFIANT
    # ========================================================================
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), nullable=False, unique=True, index=True)
    
    # ========================================================================
    # INFORMATIONS PRINCIPALES
    # ========================================================================
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_message = Column(Text, nullable=False)  # Message original brut
    
    # ========================================================================
    # STATUT ET WORKFLOW
    # ========================================================================
    status = Column(String(50), nullable=False, default="open", index=True)
    # Valeurs: open, in_progress, resolved, closed, escalated
    
    priority = Column(String(20), default="medium")
    # Valeurs: low, medium, high, critical
    
    # ========================================================================
    # RELATIONS
    # ========================================================================
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    assigned_to_tech_id = Column(Integer, ForeignKey("technicians.id"), index=True)
    
    # ========================================================================
    # DATES
    # ========================================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # ========================================================================
    # ANALYSE IA (L0 - COMPOSANT 0)
    # ========================================================================
    ai_analyzed = Column(Boolean, default=False)
    ai_suggested_category_id = Column(Integer, ForeignKey("categories.id"))
    ai_confidence_score = Column(Numeric(3, 2))  # 0.00 - 1.00
    ai_extracted_symptoms = Column(JSONB)  # ["symptom1", "symptom2", ...]
    ai_analysis_metadata = Column(JSONB)  # Métadonnées complètes
    
    # ========================================================================
    # VALIDATION UTILISATEUR
    # ========================================================================
    user_validated_summary = Column(Boolean, default=False)
    # True si l'utilisateur a validé le résumé
    
    validation_method = Column(String(50))
    # Valeurs: "auto_validate", "confirm_summary", "ask_clarification"
    
    # ========================================================================
    # HANDOFF VERS COMPOSANT 1
    # ========================================================================
    ready_for_l1 = Column(Boolean, default=False, index=True)
    # True quand le ticket est prêt pour le Composant 1
    
    handoff_to_l1_at = Column(DateTime(timezone=True))
    # Timestamp du handoff
    
    glpi_ticket_id = Column(Integer, index=True)  # ID du ticket dans GLPI
    synced_to_glpi = Column(Boolean, default=False)  # Synchronisé avec GLPI
    glpi_sync_at = Column(DateTime(timezone=True))  # Date de synchro
    glpi_last_update = Column(DateTime(timezone=True))  # Dernière MAJ depuis GLPI
    glpi_status = Column(Integer)  # Statut GLPI (1-6)

    # ========================================================================
    # RELATIONS ORM
    # ========================================================================
    category = relationship("Category", foreign_keys=[category_id], back_populates="tickets")
    created_by_user = relationship("User", back_populates="tickets")
    assigned_to_tech = relationship("Technician", back_populates="assigned_tickets")
    # ticket_solutions = relationship("TicketSolution", back_populates="ticket", cascade="all, delete-orphan")
    # interventions = relationship("Intervention", back_populates="ticket", cascade="all, delete-orphan")
    ai_suggested_category = relationship("Category", foreign_keys=[ai_suggested_category_id], back_populates="suggested_tickets")
    created_by_user = relationship("User", back_populates="created_tickets")