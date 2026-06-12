from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import Workflow
from app.repositories.workflow_repository import WorkflowRepository


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
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow

    @staticmethod
    async def update_workflow(db, workflow_id, payload):

        workflow = await WorkflowService.get_workflow(db, workflow_id)

        update_data = payload.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(workflow, key, value)

        await db.commit()
        await db.refresh(workflow)

        return workflow

    @staticmethod
    async def delete_workflow(db, workflow_id):

        workflow = await WorkflowService.get_workflow(db, workflow_id)

        await WorkflowRepository.delete(db, workflow)

        return {"message": "Workflow deleted"}
