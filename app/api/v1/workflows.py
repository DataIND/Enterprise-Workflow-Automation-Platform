from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.services.workflow_service import WorkflowService
from app.api.deps import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await WorkflowService.create_workflow(db, organization_id=1, payload=payload)


@router.get("", response_model=list[WorkflowResponse])
async def get_workflows(db: AsyncSession = Depends(get_db)):
    return await WorkflowService.list_workflows(db, organization_id=1)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    return await WorkflowService.get_workflow(db, workflow_id)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int, payload: WorkflowUpdate, db: AsyncSession = Depends(get_db)
):
    return await WorkflowService.update_workflow(db, workflow_id, payload)


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    return await WorkflowService.delete_workflow(db, workflow_id)
