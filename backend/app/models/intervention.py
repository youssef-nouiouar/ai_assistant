# ============================================================================
# FICHIER : backend/app/models/intervention.py
# DESCRIPTION : Modèle SQLAlchemy pour les interventions
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        UniqueConstraint('year', 'month', 'problem_type', 'sequential_number', name='uq_intervention_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Relations
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    solution_id = Column(Integer, ForeignKey("solutions.id"))
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    
    # Identifiant décomposé
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    problem_type = Column(String(100), nullable=False, index=True)
    sequential_number = Column(Integer, nullable=False)
    
    # Catégorisation
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Problème
    problem_title = Column(String(200), nullable=False)
    user_message = Column(Text, nullable=False)
    symptoms = Column(JSONB, nullable=False)
    
    # Solution appliquée
    solution_summary = Column(Text, nullable=False)
    solution_steps = Column(JSONB, nullable=False)
    solution_steps_count = Column(Integer, nullable=False)
    success = Column(Boolean, default=True)
    
    # Cause
    root_cause = Column(Text, nullable=False)
    
    # Médias
    screenshots = Column(JSONB)
    screenshots_count = Column(Integer, default=0)
    file_path = Column(Text)
    
    # Mots-clés
    keywords = Column(JSONB, nullable=False)
    
    # Temps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # IA / RAG
    indexed_in_chromadb = Column(Boolean, default=False)
    embedding_id = Column(String(100))
    similar_cases_count = Column(Integer, default=0)
    effectiveness_score = Column(Numeric(3, 2))
    last_indexed_at = Column(DateTime(timezone=True))
    
    # Relations
    related_interventions = Column(JSONB)
    
    # Feedback
    user_rating = Column(Integer)
    user_comment = Column(Text)
    review_status = Column(String(20), default="pending", index=True)
    reviewed_at = Column(DateTime(timezone=True))
   # reviewed_by_tech_id = Column(Integer, ForeignKey("technicians.id"))
    
    # Relations ORM
    ticket = relationship("Ticket", back_populates="interventions")
    solution = relationship("Solution", back_populates="interventions")
    technician = relationship("Technician", foreign_keys=[technician_id], back_populates="interventions")
    category = relationship("Category", back_populates="interventions")