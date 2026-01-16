# ============================================================================
# FICHIER : backend/app/models/__init__.py
# DESCRIPTION : Import centralisé des modèles
# ============================================================================

from app.models.category import Category
from app.models.user import User
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.solution import Solution
from app.models.ticket_solution import TicketSolution
from app.models.intervention import Intervention

__all__ = [
    "Category",
    "User",
    "Technician",
    "Ticket",
    "Solution",
    "TicketSolution",
    "Intervention",
]