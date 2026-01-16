# ============================================================================
# FICHIER : backend/app/models/user.py
# DESCRIPTION : Modèle SQLAlchemy pour les utilisateurs
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    department = Column(String(100))
    phone = Column(String(20))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    created_tickets = relationship("Ticket", back_populates="created_by_user")