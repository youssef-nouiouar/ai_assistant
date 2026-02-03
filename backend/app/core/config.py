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
    
    # openroutines
    OPENROUTER_API_KEY: str = "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"

    # Sécurité
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # ========================================================================
    # GLPI CONFIGURATION
    # ========================================================================

    GLPI_ENABLED: bool = True  # Activer/désactiver l'intégration GLPI
    GLPI_API_URL: str = "http://localhost/glpi/apirest.php"
    GLPI_APP_TOKEN: str = "uc00DWibqqnnfKd4mzJ5enb2dy9OlP9g6Xk7i0TG"  # À définir dans .env
    GLPI_USER_TOKEN: str = "lKoBkb0nVBfN78FzxcbKemYKIUQKPHDoBEmhRqmB"  # À définir dans .env

    # Mode de synchronisation
    # "glpi_only": Créer uniquement dans GLPI
    # "dual": Créer dans notre DB + GLPI
    GLPI_SYNC_MODE: str = "dual"

    # Webhook secret pour la vérification des signatures
    GLPI_WEBHOOK_SECRET: str = ""  # Générer avec: openssl rand -hex 32

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instance globale des settings
settings = Settings()