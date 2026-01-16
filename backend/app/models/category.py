# ============================================================================
# FICHIER : backend/app/models/category.py
# DESCRIPTION : Modèle SQLAlchemy pour les catégories (CORRIGÉ)
# ============================================================================

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    abbreviation = Column(String(10), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description = Column(Text)
    level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ========== RELATIONS ==========
    
    # Auto-référence : parent/enfants
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="subcategories",
        foreign_keys=[parent_id]
    )
    
    subcategories = relationship(
        "Category",
        back_populates="parent",
        foreign_keys=[parent_id]
    )
    
    # ✅ Tickets avec catégorie réelle
    tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.category_id",
        back_populates="category"
    )
    
    # ✅ Tickets avec catégorie suggérée par l'IA
    suggested_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.ai_suggested_category_id",
        back_populates="ai_suggested_category"
    )
    
    # Solutions
    solutions = relationship(
        "Solution",
        back_populates="category"
    )
    
    # Interventions
    interventions = relationship(
        "Intervention",
        back_populates="category"
    )