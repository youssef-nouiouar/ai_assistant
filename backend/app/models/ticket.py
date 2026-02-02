from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.category import Category


class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_message = Column(Text, nullable=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    priority = Column(String(20), default="medium")
    status = Column(String(50), default="open")
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    user_email = Column(String(255))
    
    ai_confidence_score = Column(Numeric(3, 2))
    ai_extracted_symptoms = Column(JSONB)
    validation_method = Column(String(50))
    
    glpi_ticket_id = Column(Integer, unique=True)
    synced_to_glpi = Column(Boolean, default=False)
    glpi_sync_at = Column(DateTime(timezone=True))
    glpi_last_update = Column(DateTime(timezone=True))
    
    ready_for_l1 = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relations
    category = relationship("Category", back_populates="tickets")
    created_by_user = relationship("User", back_populates="tickets")