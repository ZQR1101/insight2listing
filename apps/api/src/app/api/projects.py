"""Workspace and project lifecycle endpoints (plan sections 6.1, 7.1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import ActorDep, SessionDep
from app.audit.audit_logger import log_event
from app.core.enums import AuditAction, WorkflowState
from app.models.identity import Workspace
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectList,
    ProjectRead,
    ProjectStatusUpdate,
    WorkspaceRead,
)

router = APIRouter(prefix="/api/v1", tags=["projects"])


@router.get("/workspaces", response_model=WorkspaceRead)
async def get_default_workspace(session: SessionDep) -> WorkspaceRead:
    """Return the single default workspace (multi-tenancy comes later)."""
    ws = (await session.execute(select(Workspace).limit(1))).scalar_one_or_none()
    if ws is None:
        raise HTTPException(status_code=404, detail="no workspace configured")
    return WorkspaceRead.model_validate(ws)


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, session: SessionDep, actor: ActorDep
) -> ProjectRead:
    workspace = (
        await session.execute(select(Workspace).where(Workspace.id == payload.workspace_id))
    ).scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace not found")

    project = Project(
        workspace_id=workspace.id,
        name=payload.name,
        marketplace=payload.marketplace.value,
        target_locale=payload.target_locale,
        interface_locale=payload.interface_locale,
        currency=payload.currency,
        status=WorkflowState.DRAFT.value,
        created_by=actor,
    )
    session.add(project)
    await log_event(
        session,
        workspace_id=workspace.id,
        action=AuditAction.PROJECT_CREATED,
        actor=actor,
        entity_type="project",
        entity_id=str(project.id),
        after={"name": project.name},
    )
    await session.commit()
    await session.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/projects", response_model=ProjectList)
async def list_projects(session: SessionDep) -> ProjectList:
    total = (await session.execute(select(func.count()).select_from(Project))).scalar_one()
    rows = (await session.execute(select(Project).order_by(Project.created_at.desc()))).scalars()
    items = [ProjectRead.model_validate(p) for p in rows]
    return ProjectList(items=items, total=total)


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: uuid.UUID, session: SessionDep) -> ProjectRead:
    project = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectRead.model_validate(project)


@router.patch("/projects/{project_id}/status", response_model=ProjectRead)
async def update_project_status(
    project_id: uuid.UUID, payload: ProjectStatusUpdate, session: SessionDep, actor: ActorDep
) -> ProjectRead:
    project = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    before = {"status": project.status}
    project.status = payload.status.value
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.PROJECT_STATUS_CHANGED,
        actor=actor,
        entity_type="project",
        entity_id=str(project.id),
        before=before,
        after={"status": project.status},
    )
    await session.commit()
    await session.refresh(project)
    return ProjectRead.model_validate(project)
