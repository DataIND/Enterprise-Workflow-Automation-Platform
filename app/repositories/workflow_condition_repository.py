from sqlalchemy import select

from app.db.models.workflow_condition import WorkflowCondition


class WorkflowConditionRepository:

    @staticmethod
    async def create(db, condition: WorkflowCondition):
        db.add(condition)
        await db.commit()
        await db.refresh(condition)

        return condition

    @staticmethod
    async def get_by_workflow(db, workflow_id: int):
        result = await db.execute(
            select(WorkflowCondition)
            .where(WorkflowCondition.workflow_id == workflow_id)
            .order_by(WorkflowCondition.id)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(db, condition_id: int):
        result = await db.execute(
            select(WorkflowCondition).where(WorkflowCondition.id == condition_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db, condition: WorkflowCondition):
        await db.delete(condition)
        await db.commit()
