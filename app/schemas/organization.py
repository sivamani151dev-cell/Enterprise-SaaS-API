from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class OrgCreate(BaseModel):
    name: str
    description: Optional[str] = None


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class OrgResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True