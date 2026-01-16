# ============================================================================
# FICHIER : backend/app/api/deps.py
# DESCRIPTION : Dépendances pour les routes API
# ============================================================================

from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import get_db

# Ré-export de get_db pour utilisation dans les routes
def get_database() -> Generator[Session, None, None]:
    """
    Dépendance pour obtenir une session de base de données
    """
    yield from get_db()