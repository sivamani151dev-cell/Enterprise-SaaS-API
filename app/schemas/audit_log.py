from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Any


class AuditLogResponse(BaseModel):
    id: UUID
    org_id: UUID
    actor_id: UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True