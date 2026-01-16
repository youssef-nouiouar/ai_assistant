# ============================================================================
# FICHIER : backend/app/models/technician.py
# DESCRIPTION : Modèle SQLAlchemy pour les techniciens
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Technician(Base):
    __tablename__ = "technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    tech_id = Column(String(20), nullable=False, unique=True, index=True) # a remove if not needed
    role = Column(String(50), default="technician")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    assigned_tickets = relationship("Ticket", back_populates="assigned_to_tech")
    interventions = relationship("Intervention", back_populates="technician")