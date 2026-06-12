from datetime import datetime


from app.db.models.workflow_execution import WorkflowExecution


from app.repositories.execution_repository import ExecutionRepository


class ExecutionService:

    @staticmethod
    async def start_execution(db, workflow_id, payload):

        execution = WorkflowExecution(
            workflow_id=workflow_id, event_payload=payload, status="RUNNING"
        )

        return await ExecutionRepository.create(db, execution)

    @staticmethod
    async def mark_success(db, execution):

        execution.status = "SUCCESS"

        execution.completed_at = datetime.utcnow()

        await db.commit()

    @staticmethod
    async def mark_failed(db, execution, error):

        execution.status = "FAILED"

        execution.error_message = str(error)

        await db.commit()
