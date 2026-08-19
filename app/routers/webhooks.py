from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.webhook import Webhook
from app.models.membership import MemberRole
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookResponse
from app.routers.dependencies import require_org_role
from app.core.exceptions import NotFoundException
from app.core.logging import get_logger

router = APIRouter(prefix="/orgs/{org_slug}/webhooks", tags=["Webhooks"])
logger = get_logger(__name__)


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(
    payload: WebhookCreate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    webhook = Webhook(
        org_id=org.id,
        url=str(payload.url),
        events=",".join(payload.events)
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    return db.query(Webhook).filter(
        Webhook.org_id == org.id,
        Webhook.is_active == True
    ).all()


@router.patch("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: str,
    payload: WebhookUpdate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.org_id == org.id
    ).first()
    if not webhook:
        raise NotFoundException("Webhook")

    if payload.url:
        webhook.url = str(payload.url)
    if payload.events:
        webhook.events = ",".join(payload.events)
    if payload.is_active is not None:
        webhook.is_active = payload.is_active

    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.org_id == org.id
    ).first()
    if not webhook:
        raise NotFoundException("Webhook")
    db.delete(webhook)
    db.commit()