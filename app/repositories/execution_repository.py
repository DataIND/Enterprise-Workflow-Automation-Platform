from sqlalchemy import select


from app.db.models.workflow_execution import WorkflowExecution


class ExecutionRepository:

    @staticmethod
    async def create(db, execution):

        db.add(execution)

        await db.commit()

        await db.refresh(execution)

        return execution

    @staticmethod
    async def get_all(db):

        result = await db.execute(select(WorkflowExecution))

        return result.scalars().all()
