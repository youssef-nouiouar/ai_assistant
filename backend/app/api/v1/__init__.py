# ============================================================================
# FICHIER : backend/app/api/v1/__init__.py
# DESCRIPTION : Router principal API v1
# ============================================================================

from fastapi import APIRouter
from app.api.v1 import tickets, categories

api_router = APIRouter()

api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])