from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.membership import MemberRole


class MemberInvite(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: MemberRole


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    role: MemberRole
    created_at: datetime

    class Config:
        from_attributes = True