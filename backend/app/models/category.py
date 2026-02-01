# ============================================================================
# FICHIER : backend/app/models/category.py
# DESCRIPTION : Modèle SQLAlchemy pour les catégories
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(20), nullable=False, unique=True)
    level = Column(Integer, nullable=False, default=2)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    glpi_category_id = Column(Integer, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    parent = relationship("Category", remote_side=[id], backref="children")
    tickets = relationship("Ticket", back_populates="category")
