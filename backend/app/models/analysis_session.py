from sqlalchemy import Column, String, Integer, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ai_summary = Column(JSONB)
    original_message = Column(String, nullable=False)
    confidence_score = Column(Numeric(3, 2))
    status = Column(String(20), default="pending")
    user_email = Column(String(255))
    clarification_attempts = Column(Integer, default=0)
    parent_session_id = Column(String(36))
    selected_choice_id = Column(String(50), nullable=True)
    action_type = Column(String(50))
    ticket_id = Column(Integer)