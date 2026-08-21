from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.workflow_action import (
    WorkflowActionCreate,
    WorkflowActionResponse,
    WorkflowActionUpdate,
)
from app.services.action_service import ActionService
from app.services.workflow_service import WorkflowService
from app.utils.enums import UserRole

router = APIRouter(
    prefix="/workflows/{workflow_id}/actions", tags=["Workflow Actions"]
)


@router.post(
    "", response_model=WorkflowActionResponse, status_code=status.HTTP_201_CREATED
)
async def create_action(
    workflow_id: int,
    payload: WorkflowActionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ActionService.create_action(db, workflow_id, payload)


@router.get("", response_model=list[WorkflowActionResponse])
async def list_actions(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.MEMBER
    )

    return await ActionService.list_actions(db, workflow_id)


@router.get("/{action_id}", response_model=WorkflowActionResponse)
async def get_action(
    workflow_id: int,
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.MEMBER
    )

    return await ActionService.get_action(db, workflow_id, action_id)


@router.patch("/{action_id}", response_model=WorkflowActionResponse)
async def update_action(
    workflow_id: int,
    action_id: int,
    payload: WorkflowActionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ActionService.update_action(db, workflow_id, action_id, payload)


@router.delete("/{action_id}")
async def delete_action(
    workflow_id: int,
    action_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ActionService.delete_action(db, workflow_id, action_id)
