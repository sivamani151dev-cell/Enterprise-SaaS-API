from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.project import Project
from app.models.membership import MemberRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.routers.dependencies import require_org_role
from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.cache.redis import cache_delete, CacheKeys

router = APIRouter(prefix="/orgs/{org_slug}/projects", tags=["Projects"])
logger = get_logger(__name__)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    project = Project(org_id=org.id, **payload.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    await cache_delete(CacheKeys.org_projects(org.slug))
    return project


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    return db.query(Project).filter(
        Project.org_id == org.id,
        Project.is_active == True
    ).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == org.id
    ).first()
    if not project:
        raise NotFoundException("Project")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == org.id
    ).first()
    if not project:
        raise NotFoundException("Project")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == org.id
    ).first()
    if not project:
        raise NotFoundException("Project")
    project.is_active = False
    db.commit()