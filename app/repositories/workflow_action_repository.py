from sqlalchemy import select

from app.db.models.workflow_action import WorkflowAction


class WorkflowActionRepository:

    async def create(self, db, action):

        db.add(action)

        await db.commit()

        await db.refresh(action)

        return action

    async def get_by_workflow(self, db, workflow_id: int):

        result = await db.execute(
            select(WorkflowAction)
            .where(WorkflowAction.workflow_id == workflow_id)
            .order_by(WorkflowAction.execution_order)
        )

        return result.scalars().all()
