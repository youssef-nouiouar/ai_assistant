# ============================================================================
# FICHIER : backend/app/api/v1/categories.py
# DESCRIPTION : Routes API pour les catégories
# ============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.api.deps import get_database
from app.models.category import Category

router = APIRouter()

class CategoryResponse(BaseModel):
    id: int
    name: str
    abbreviation: str
    parent_id: Optional[int] = None  # ID de la catégorie parente (si applicable)
    level: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_database),
    level: int = None
):
    """
    Lister toutes les catégories
    
    Query params:
    - level: Filtrer par niveau (1 = catégories principales, 2 = sous-catégories)
    """
    query = db.query(Category)
    
    if level:
        query = query.filter(Category.level == level)
    
    categories = query.order_by(Category.level, Category.name).all()
    
    return categories