from fastapi import FastAPI
from app.routers import (
    auth, organizations, members,
    projects, tasks, api_keys,
    webhooks, audit_logs
)


def register_routers(app: FastAPI) -> None:
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1")
    app.include_router(members.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(api_keys.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(audit_logs.router, prefix="/api/v1")