from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.permissions import require_org_role
from app.db.session import get_db
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate
from app.services.workflow_service import WorkflowService
from app.utils.enums import UserRole

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await require_org_role(db, user_id, payload.organization_id, UserRole.ADMIN)

    return await WorkflowService.create_workflow(
        db, organization_id=payload.organization_id, payload=payload
    )


@router.get("", response_model=list[WorkflowResponse])
async def get_workflows(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await require_org_role(db, user_id, organization_id, UserRole.MEMBER)

    return await WorkflowService.list_workflows(db, organization_id)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.MEMBER
    )


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    payload: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    workflow = await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await WorkflowService.update_workflow(db, workflow, payload)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    workflow = await WorkflowService.get_workflow_for_user(
        db, workflow_id, user_id, UserRole.ADMIN
    )

    return await WorkflowService.delete_workflow(db, workflow)
