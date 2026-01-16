# ============================================================================
# FICHIER : backend/app/models/ticket.py
# DESCRIPTION : Modèle SQLAlchemy pour les tickets (CORRIGÉ)
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="open", index=True)
    priority = Column(String(20), default="medium")
    
    # ========== CLÉS ÉTRANGÈRES ==========
    # Catégorie réelle (sélectionnée par l'utilisateur/technicien)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Catégorie suggérée par l'IA (OPTIONNEL)
    ai_suggested_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Utilisateur qui a créé le ticket
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Technicien assigné
    assigned_to_tech_id = Column(Integer, ForeignKey("technicians.id"), nullable=True, index=True)
    
    # ========== DATES ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ========== MÉTADONNÉES IA ==========
    ai_analyzed = Column(Boolean, default=False)
    ai_confidence_score = Column(Numeric(3, 2), nullable=True)
    ai_extracted_symptoms = Column(JSONB, nullable=True)
    
    # ========== RELATIONS ORM ==========
    # ✅ Catégorie réelle (EXPLICITE : foreign_keys=[category_id])
    category = relationship("Category",foreign_keys=[category_id],back_populates="tickets")
    
    # ✅ Catégorie suggérée par l'IA (EXPLICITE : foreign_keys=[ai_suggested_category_id])
    ai_suggested_category = relationship("Category",foreign_keys=[ai_suggested_category_id],back_populates="suggested_tickets")
    
    # Utilisateur qui a créé le ticket
    created_by_user = relationship("User",foreign_keys=[created_by_user_id],back_populates="created_tickets")
    
    # Technicien assigné
    assigned_to_tech = relationship("Technician",foreign_keys=[assigned_to_tech_id],back_populates="assigned_tickets")
    
    # Relations many-to-many
    ticket_solutions = relationship("TicketSolution",back_populates="ticket",cascade="all, delete-orphan")
    
    interventions = relationship("Intervention",back_populates="ticket",cascade="all, delete-orphan")