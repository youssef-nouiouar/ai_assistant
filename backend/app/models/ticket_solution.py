# ============================================================================
# FICHIER : backend/app/models/ticket_solution.py
# DESCRIPTION : Modèle SQLAlchemy pour la table d'association ticket_solutions
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class TicketSolution(Base):
    __tablename__ = "ticket_solutions"
    __table_args__ = (
        UniqueConstraint('ticket_id', 'solution_id', name='uq_ticket_solution'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    solution_id = Column(Integer, ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ordre de proposition
    suggestion_order = Column(Integer, nullable=False)
    
    # Application
    applied = Column(Boolean, default=False, index=True)
    applied_at = Column(DateTime(timezone=True))
    applied_by_tech_id = Column(Integer, ForeignKey("technicians.id"))
    
    # Résultat
    success = Column(Boolean, index=True)
    resolution_time_minutes = Column(Integer)
    
    # Feedback
    user_feedback_rating = Column(Integer)
    user_feedback_comment = Column(Text)
    
    # Métadonnées IA
    ai_confidence_score = Column(Numeric(3, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    ticket = relationship("Ticket", back_populates="ticket_solutions")
    solution = relationship("Solution", back_populates="ticket_solutions")