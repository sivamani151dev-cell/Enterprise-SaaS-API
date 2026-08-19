from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.membership import Membership, MemberRole
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.membership import MemberInvite, MemberRoleUpdate, MemberResponse
from app.routers.dependencies import get_current_user, require_org_role
from app.core.exceptions import NotFoundException, ConflictException
from app.core.logging import get_logger
from app.cache.redis import cache_delete, CacheKeys
from app.workers.tasks.emails import send_invitation_email
from typing import List

router = APIRouter(prefix="/orgs/{org_slug}/members", tags=["Members"])
logger = get_logger(__name__)


@router.get("", response_model=List[MemberResponse])
def list_members(
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    return db.query(Membership).filter(Membership.org_id == org.id).all()


@router.post("/invite", status_code=202)
async def invite_member(
    payload: MemberInvite,
    request: Request,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    inviter = context["user"]

    invitee = db.query(User).filter(User.email == payload.email).first()
    if not invitee:
        raise NotFoundException("User")

    existing = db.query(Membership).filter(
        Membership.user_id == invitee.id,
        Membership.org_id == org.id
    ).first()
    if existing:
        raise ConflictException("User is already a member")

    membership = Membership(
        user_id=invitee.id,
        org_id=org.id,
        role=payload.role
    )
    db.add(membership)

    audit = AuditLog(
        org_id=org.id,
        actor_id=inviter.id,
        action="member.invited",
        resource_type="membership",
        resource_id=str(invitee.id),
        new_value={"email": payload.email, "role": payload.role},
        ip_address=request.client.host
    )
    db.add(audit)
    db.commit()

    # Invalidate members cache
    await cache_delete(CacheKeys.org_members(org.slug))

    # Send email async
    send_invitation_email.delay(
        invitee.email,
        inviter.full_name,
        org.name,
        org.slug
    )

    return {"message": "Invitation sent", "email": payload.email}


@router.patch("/{user_id}/role", response_model=MemberResponse)
def update_role(
    user_id: str,
    payload: MemberRoleUpdate,
    context=Depends(require_org_role(MemberRole.OWNER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.org_id == org.id
    ).first()
    if not membership:
        raise NotFoundException("Member")

    membership.role = payload.role
    db.commit()
    db.refresh(membership)
    return membership


@router.delete("/{user_id}", status_code=204)
async def remove_member(
    user_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.org_id == org.id
    ).first()
    if not membership:
        raise NotFoundException("Member")

    db.delete(membership)
    db.commit()
    await cache_delete(CacheKeys.org_members(org.slug))