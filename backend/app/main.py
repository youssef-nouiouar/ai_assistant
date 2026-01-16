# ============================================================================
# FICHIER : backend/app/main.py
# DESCRIPTION : Point d'entrée de l'application FastAPI
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_router
from app.core.database import engine, Base

# Créer les tables (en développement uniquement)
Base.metadata.create_all(bind=engine)

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API pour l'assistant IT intelligent",
    docs_url="/docs",
    redoc_url="/redoc"
)

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