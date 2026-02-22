# ============================================================================
# FICHIER : backend/app/api/deps.py
# DESCRIPTION : Dépendances pour les routes API
# ============================================================================

from typing import Generator
from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings


def get_database() -> Generator[Session, None, None]:
    """Dépendance pour obtenir une session de base de données"""
    yield from get_db()


async def verify_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    """
    Vérifie la clé API sur les endpoints workflow.

    - Si API_KEY est vide dans la config, la vérification est ignorée
      (développement / rétrocompatibilité).
    - Si API_KEY est défini, le header X-API-Key doit correspondre exactement.

    Note : combiner avec une isolation réseau (intranet) en production,
    car la clé est transmise depuis le bundle JavaScript du navigateur.
    """
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
        )
