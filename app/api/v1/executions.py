from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.permissions import require_org_role
from app.db.session import get_db
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.execution import ExecutionResponse
from app.utils.enums import UserRole, WorkflowStatus

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("", response_model=list[ExecutionResponse])
async def list_executions(
    organization_id: int,
    status_filter: WorkflowStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await require_org_role(db, user_id, organization_id, UserRole.MEMBER)

    return await ExecutionRepository.get_by_organization(
        db,
        organization_id,
        status=status_filter.value if status_filter else None,
        page=page,
        size=size,
    )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    execution = await ExecutionRepository.get_by_id(db, execution_id)

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    organization_id = await ExecutionRepository.get_organization_id(db, execution)

    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    await require_org_role(db, user_id, organization_id, UserRole.MEMBER)

    return execution
