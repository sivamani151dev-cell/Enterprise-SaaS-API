from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.organization import Organization
from app.models.membership import Membership, MemberRole
from app.models.audit_log import AuditLog
from app.schemas.organization import OrgCreate, OrgUpdate, OrgResponse
from app.routers.dependencies import get_current_user, require_org_role
from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.cache.redis import cache_get, cache_set, cache_delete, CacheKeys
from app.workers.tasks.emails import send_welcome_email
from app.models.user import User
import json
import re

router = APIRouter(prefix="/orgs", tags=["Organizations"])
logger = get_logger(__name__)


def make_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


@router.post("", response_model=OrgResponse, status_code=201)
def create_org(
    payload: OrgCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slug = make_slug(payload.name)
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise ConflictException("Organization name already taken")

    org = Organization(
        name=payload.name,
        slug=slug,
        description=payload.description
    )
    db.add(org)
    db.flush()

    # Auto-add creator as owner
    membership = Membership(
        user_id=current_user.id,
        org_id=org.id,
        role=MemberRole.OWNER
    )
    db.add(membership)

    # Audit log
    audit = AuditLog(
        org_id=org.id,
        actor_id=current_user.id,
        action="org.created",
        resource_type="organization",
        resource_id=str(org.id),
        new_value={"name": org.name, "slug": org.slug},
        ip_address=request.client.host
    )
    db.add(audit)
    db.commit()
    db.refresh(org)

    # Send welcome email async
    send_welcome_email.delay(
        current_user.email,
        current_user.full_name,
        org.name
    )

    logger.info("Org created", extra={
        "org_id": str(org.id),
        "user_id": str(current_user.id)
    })
    return org


@router.get("/{org_slug}", response_model=OrgResponse)
async def get_org(
    org_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check cache first
    cached = await cache_get(CacheKeys.org(org_slug))
    if cached:
        return json.loads(cached)

    org = db.query(Organization).filter(Organization.slug == org_slug).first()
    if not org:
        raise NotFoundException("Organization")

    org_data = OrgResponse.from_orm(org).dict()
    await cache_set(CacheKeys.org(org_slug), json.dumps(org_data, default=str))
    return org


@router.patch("/{org_slug}", response_model=OrgResponse)
async def update_org(
    org_slug: str,
    payload: OrgUpdate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    old_data = {"name": org.name, "description": org.description}

    if payload.name:
        org.name = payload.name
    if payload.description is not None:
        org.description = payload.description

    db.commit()
    db.refresh(org)

    # Invalidate cache
    await cache_delete(CacheKeys.org(org_slug))

    logger.info("Org updated", extra={"org_id": str(org.id)})
    return org


@router.delete("/{org_slug}", status_code=204)
async def delete_org(
    org_slug: str,
    context=Depends(require_org_role(MemberRole.OWNER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    org.is_active = False
    db.commit()
    await cache_delete(CacheKeys.org(org_slug))
    logger.info("Org deactivated", extra={"org_id": str(org.id)})