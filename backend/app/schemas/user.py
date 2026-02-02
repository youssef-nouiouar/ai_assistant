from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    glpi_user_id: Optional[int] = None


class UserRead(UserBase):
    id: int
    glpi_user_id: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True