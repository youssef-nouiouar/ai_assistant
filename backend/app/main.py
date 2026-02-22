# ============================================================================
# FICHIER : backend/app/main.py
# DESCRIPTION : Point d'entrée de l'application FastAPI
# ============================================================================

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.v1 import api_router
from app.core.database import engine, Base

# Créer les tables (en développement uniquement)
Base.metadata.create_all(bind=engine)
from app.api.v1 import glpi_webhook

# Rate limiter (partagé avec les routes via state)
limiter = Limiter(key_func=get_remote_address)

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API pour l'assistant IT intelligent",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attacher le limiter à l'app (requis par slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes API v1
app.include_router(api_router, prefix="/api/v1")

# Serve uploaded files (screenshots, attachments)
_upload_dir = Path(settings.UPLOAD_DIR)
_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_dir)), name="uploads")

@app.get("/")
def read_root():
    """
    Route racine
    """
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
def health_check():
    """
    Endpoint de health check
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )