from sqlalchemy import select

from app.db.models.workflow_condition import WorkflowCondition


class WorkflowConditionRepository:

    async def get_by_workflow(self, db, workflow_id):

        result = await db.execute(
            select(WorkflowCondition).where(
                WorkflowCondition.workflow_id == workflow_id
            )
        )

        return result.scalars().all()
