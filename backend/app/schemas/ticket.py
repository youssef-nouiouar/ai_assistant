from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    user_message: str
    category_id: Optional[int] = None
    priority: str = "medium"


class TicketCreate(TicketBase):
    user_email: Optional[str] = None


class TicketRead(TicketBase):
    id: int
    ticket_number: str
    status: str
    glpi_ticket_id: Optional[int]
    synced_to_glpi: bool
    ready_for_L1: bool
    created_at: datetime
    
    class Config:
        from_attributes = True