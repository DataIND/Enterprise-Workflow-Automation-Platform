from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_org_role
from app.db.models.workflow import Workflow
from app.repositories.workflow_repository import WorkflowRepository
from app.utils.enums import UserRole


class WorkflowService:

    @staticmethod
    async def create_workflow(db: AsyncSession, organization_id: int, payload):
        workflow = Workflow(
            organization_id=organization_id,
            name=payload.name,
            description=payload.description,
            trigger_type=payload.trigger_type,
        )

        return await WorkflowRepository.create(db, workflow)

    @staticmethod
    async def list_workflows(db, organization_id):

        return await WorkflowRepository.get_all(db, organization_id)

    @staticmethod
    async def get_workflow(db, workflow_id):

        workflow = await WorkflowRepository.get_by_id(db, workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        return workflow

    @staticmethod
    async def get_workflow_for_user(
        db,
        workflow_id: int,
        user_id: int,
        minimum_role: UserRole = UserRole.MEMBER,
    ) -> Workflow:
        """Load a workflow and verify the caller's role in its organization."""

        workflow = await WorkflowService.get_workflow(db, workflow_id)

        await require_org_role(db, user_id, workflow.organization_id, minimum_role)

        return workflow

    @staticmethod
    async def update_workflow(db, workflow: Workflow, payload):

        update_data = payload.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(workflow, key, value)

        await db.commit()
        await db.refresh(workflow)

        return workflow

    @staticmethod
    async def delete_workflow(db, workflow: Workflow):

        await WorkflowRepository.delete(db, workflow)

        return {"message": "Workflow deleted"}
