from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import List, Optional


VALID_EVENTS = [
    "member.invited",
    "member.removed",
    "project.created",
    "task.completed",
    "api_key.revoked"
]


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: UUID
    org_id: UUID
    url: str
    events: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True