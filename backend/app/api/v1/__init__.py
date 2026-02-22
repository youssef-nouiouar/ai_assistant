# ============================================================================
# FICHIER : backend/app/api/v1/__init__.py
# DESCRIPTION : Router principal API v1 mis à jour
# ============================================================================

from fastapi import APIRouter
from app.api.v1 import ticket_workflow
from app.api.v1 import glpi_webhook
from app.api.v1 import upload

api_router = APIRouter()

api_router.include_router(glpi_webhook.router, prefix="/glpi-webhook", tags=["glpi-webhook"])
api_router.include_router(ticket_workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(upload.router, prefix="/workflow", tags=["upload"])