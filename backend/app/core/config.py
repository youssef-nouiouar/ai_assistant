from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://it_admin:secure_password_123@localhost:5432/ai_it_assistant"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_API_KEY="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"
    
    # GLPI
    GLPI_ENABLED: bool = True
    GLPI_API_URL: str
    GLPI_APP_TOKEN: str
    GLPI_USER_TOKEN: str
    GLPI_SYNC_MODE: str = "dual"
    GLPI_WEBHOOK_SECRET: str = "my_secret_key_2026" #is the the truth secret 😅

    # Application
    APP_NAME: str = "AI IT Assistant"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:5173"

    # 👉 VARIABLES .env SUPPLÉMENTAIRES (qui causaient l’erreur)
    CHROMADB_PATH: str | None = None
    USE_OLLAMA: bool | None = None
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_MODEL: str | None = None

    SECRET_KEY: str | None = None
    ENVIRONMENT: str | None = None
    LOG_LEVEL: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"   # IMPORTANT


settings = Settings()
