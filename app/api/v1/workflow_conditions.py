from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.workflow_condition import (
    WorkflowConditionCreate,
    WorkflowConditionResponse,
    WorkflowConditionUpdate,
)
from app.services.condition_service import ConditionService
from app.services.workflow_service import WorkflowService
from app.utils.enums import UserRole

router = APIRouter(
    prefix="/workflows/{workflow_id}/conditions", tags=["Workflow Conditions"]
)


@router.post(
    "", response_model=WorkflowConditionResponse, status_code=status.HTTP_201_CREATED
)
async def create_condition(
    workflow_id: int,
    payload: WorkflowConditionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ConditionService.create_condition(db, workflow_id, payload)


@router.get("", response_model=list[WorkflowConditionResponse])
async def list_conditions(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.MEMBER
    )

    return await ConditionService.list_conditions(db, workflow_id)


@router.get("/{condition_id}", response_model=WorkflowConditionResponse)
async def get_condition(
    workflow_id: int,
    condition_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.MEMBER
    )

    return await ConditionService.get_condition(db, workflow_id, condition_id)


@router.patch("/{condition_id}", response_model=WorkflowConditionResponse)
async def update_condition(
    workflow_id: int,
    condition_id: int,
    payload: WorkflowConditionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ConditionService.update_condition(
        db, workflow_id, condition_id, payload
    )


@router.delete("/{condition_id}")
async def delete_condition(
    workflow_id: int,
    condition_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await ConditionService.delete_condition(db, workflow_id, condition_id)
