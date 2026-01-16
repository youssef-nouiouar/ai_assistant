# ============================================================================
# FICHIER : backend/app/models/solution.py
# DESCRIPTION : Modèle SQLAlchemy pour les solutions
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Solution(Base):
    __tablename__ = "solutions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    steps = Column(JSONB, nullable=False)
    
    # Catégorisation
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Efficacité
    times_applied = Column(Integer, default=0)
    times_successful = Column(Integer, default=0)
    avg_resolution_time_minutes = Column(Integer)
    
    # Métadonnées
    keywords = Column(JSONB, nullable=False)
    tags = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # IA / RAG
    indexed_in_chromadb = Column(Boolean, default=False, index=True)
    embedding_id = Column(String(100))
    last_indexed_at = Column(DateTime(timezone=True))
    
    # Relations
    category = relationship("Category", back_populates="solutions")
    ticket_solutions = relationship("TicketSolution", back_populates="solution")
    interventions = relationship("Intervention", back_populates="solution")