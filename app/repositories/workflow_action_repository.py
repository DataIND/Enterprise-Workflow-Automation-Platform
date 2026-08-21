from sqlalchemy import select

from app.db.models.workflow_action import WorkflowAction


class WorkflowActionRepository:

    @staticmethod
    async def create(db, action: WorkflowAction):
        db.add(action)
        await db.commit()
        await db.refresh(action)

        return action

    @staticmethod
    async def get_by_workflow(db, workflow_id: int):
        result = await db.execute(
            select(WorkflowAction)
            .where(WorkflowAction.workflow_id == workflow_id)
            .order_by(WorkflowAction.execution_order)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(db, action_id: int):
        result = await db.execute(
            select(WorkflowAction).where(WorkflowAction.id == action_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db, action: WorkflowAction):
        await db.delete(action)
        await db.commit()
