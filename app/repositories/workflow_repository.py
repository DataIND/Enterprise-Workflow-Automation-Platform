from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import Workflow


class WorkflowRepository:

    @staticmethod
    async def create(db: AsyncSession, workflow: Workflow):
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)

        return workflow

    @staticmethod
    async def get_all(db: AsyncSession, organization_id: int):
        result = await db.execute(
            select(Workflow).where(Workflow.organization_id == organization_id)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, workflow_id: int):
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))

        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, workflow: Workflow):
        await db.delete(workflow)
        await db.commit()
