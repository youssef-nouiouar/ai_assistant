from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    name: str
    abbreviation: str
    level: int = 2
    parent_id: Optional[int] = None
    glpi_category_id: Optional[int] = None
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
