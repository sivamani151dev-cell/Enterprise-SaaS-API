from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.models.membership import MemberRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.routers.dependencies import require_org_role
from app.core.exceptions import NotFoundException
from app.core.logging import get_logger

router = APIRouter(
    prefix="/orgs/{org_slug}/projects/{project_id}/tasks",
    tags=["Tasks"]
)
logger = get_logger(__name__)


def get_project_or_404(project_id: str, org_id: str, db: Session) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == org_id
    ).first()
    if not project:
        raise NotFoundException("Project")
    return project


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    project_id: str,
    payload: TaskCreate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    get_project_or_404(project_id, str(org.id), db)
    task = Task(project_id=project_id, **payload.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: str,
    status: Optional[TaskStatus] = None,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    org = context["org"]
    get_project_or_404(project_id, str(org.id), db)
    query = db.query(Task).filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    return query.all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: str,
    task_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    if not task:
        raise NotFoundException("Task")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: str,
    task_id: str,
    payload: TaskUpdate,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    if not task:
        raise NotFoundException("Task")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    project_id: str,
    task_id: str,
    context=Depends(require_org_role(MemberRole.OWNER, MemberRole.ADMIN)),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.project_id == project_id
    ).first()
    if not task:
        raise NotFoundException("Task")
    db.delete(task)
    db.commit()