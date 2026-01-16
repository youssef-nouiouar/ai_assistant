# ============================================================================
# FICHIER : backend/app/core/database.py
# DESCRIPTION : Configuration connexion PostgreSQL avec SQLAlchemy
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# Créer l'engine SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    echo=settings.DEBUG,  # Log SQL queries en mode debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session DB
    Usage:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialiser la base de données
    Crée toutes les tables définies par les modèles
    """
    Base.metadata.create_all(bind=engine)