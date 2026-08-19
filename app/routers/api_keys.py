import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.api_key import APIKey
from app.models.membership import MemberRole
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse
from app.routers.dependencies import require_org_role
from app.core.security import hash_password
from app.core.exceptions import NotFoundException
from app.core.logging import get_logger

router = APIRouter(prefix="/orgs/{org_slug}/api-keys", tags=["API Keys"])
logger = get_logger(__name__)


@router.post("", response_model=APIKeyCreatedResponse, status_code=201)
def create_api_key(
    payload: APIKeyCreate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    user = context["user"]

    # Generate key: prefix (8 chars) + secret (32 chars)
    raw_key = secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    key_hash = hash_password(raw_key)

    api_key = APIKey(
        org_id=org.id,
        created_by_id=user.id,
        name=payload.name,
        key_hash=key_hash,
        prefix=prefix,
        expires_at=payload.expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    logger.info("API key created", extra={
        "org_id": str(org.id),
        "key_prefix": prefix
    })

    return {**APIKeyResponse.from_orm(api_key).dict(), "full_key": raw_key}


@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    return db.query(APIKey).filter(
        APIKey.org_id == org.id,
        APIKey.is_active == True
    ).all()


@router.delete("/{key_id}", status_code=204)
def revoke_api_key(
    key_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.org_id == org.id
    ).first()
    if not api_key:
        raise NotFoundException("API Key")

    api_key.is_active = False
    db.commit()
    logger.info("API key revoked", extra={"key_id": key_id})