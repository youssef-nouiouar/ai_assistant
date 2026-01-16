# ============================================================================
# FICHIER : backend/app/config.py
# DESCRIPTION : Configuration centrale de l'application
# ============================================================================

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """
    Configuration de l'application
    Lit les variables d'environnement depuis .env
    """
    
    # Application
    APP_NAME: str = "AI IT Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Base de données PostgreSQL
    DATABASE_URL: str
    
    # ChromaDB
    CHROMADB_PATH: str = "./chromadb_data"
    
    # IA
    OPENAI_API_KEY: str = ""
    USE_OLLAMA: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # Sécurité
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instance globale des settings
settings = Settings()