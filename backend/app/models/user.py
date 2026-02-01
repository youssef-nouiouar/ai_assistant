# ============================================================================
# FICHIER : backend/app/models/user.py
# DESCRIPTION : Modèle SQLAlchemy pour les utilisateurs
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    glpi_user_id = Column(Integer, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relations
    tickets = relationship("Ticket", back_populates="created_by_user")
