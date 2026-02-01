# ============================================================================
# FICHIER : backend/app/core/config.py (Ajouts pour GLPI)
# ============================================================================

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... (configurations existantes)
    
    # ========================================================================
    # GLPI CONFIGURATION
    # ========================================================================
    
    GLPI_ENABLED: bool = True  # Activer/désactiver l'intégration GLPI
    GLPI_API_URL: str = "http://localhost/glpi/apirest.php"
    GLPI_APP_TOKEN: str = ""  # À définir dans .env
    GLPI_USER_TOKEN: str = ""  # À définir dans .env
    
    # Mode de synchronisation
    # "glpi_only": Créer uniquement dans GLPI
    # "dual": Créer dans notre DB + GLPI
    GLPI_SYNC_MODE: str = "dual"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()