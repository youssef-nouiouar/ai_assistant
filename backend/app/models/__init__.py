# ============================================================================
# FICHIER : backend/app/models/__init__.py
# DESCRIPTION : Import centralisé des modèles
# ============================================================================

from app.models.base import Base
from app.models.category import Category
from app.models.user import User
from app.models.analysis_session import AnalysisSession
from app.models.ticket import Ticket

__all__ = ["Base", "Category", "User", "AnalysisSession", "Ticket"]


