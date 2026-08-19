from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.membership import MemberRole
from app.schemas.audit_log import AuditLogResponse
from app.routers.dependencies import require_org_role

router = APIRouter(prefix="/orgs/{org_slug}/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    query = db.query(AuditLog).filter(AuditLog.org_id == org.id)

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()