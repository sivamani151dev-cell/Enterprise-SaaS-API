from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    # Only returned ONCE on creation — full key never stored
    full_key: str