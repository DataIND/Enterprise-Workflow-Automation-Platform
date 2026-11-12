"""Execution lifecycle, used by the consumer and the Celery workers.

These are synchronous on purpose: Celery prefork workers and the pika consumer
have no event loop. The API only ever reads executions, through
:class:`app.repositories.execution_repository.ExecutionRepository`.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.workflow_execution import WorkflowExecution
from app.utils.enums import WorkflowStatus


class ExecutionService:

    @staticmethod
    def start_execution(
        session,
        workflow_id: int,
        event_payload: dict,
        event_id: str | None = None,
    ) -> WorkflowExecution | None:
        """Create a PENDING execution, or return None if it already exists.

        The unique (workflow_id, event_id) constraint makes a redelivered
        message a no-op instead of a second run of the same workflow.
        """

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            event_id=event_id,
            event_payload=event_payload,
            status=WorkflowStatus.PENDING.value,
        )

        session.add(execution)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return None

        session.refresh(execution)

        return execution

    @staticmethod
    def get(session, execution_id: int) -> WorkflowExecution | None:
        return session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        ).scalar_one_or_none()

    @staticmethod
    def mark_running(session, execution: WorkflowExecution) -> WorkflowExecution:
        execution.status = WorkflowStatus.RUNNING.value
        session.commit()
        session.refresh(execution)

        return execution

    @staticmethod
    def mark_success(session, execution: WorkflowExecution) -> WorkflowExecution:
        execution.status = WorkflowStatus.SUCCESS.value
        execution.completed_at = datetime.utcnow()
        session.commit()
        session.refresh(execution)

        return execution

    @staticmethod
    def mark_failed(session, execution: WorkflowExecution, error) -> WorkflowExecution:
        execution.status = WorkflowStatus.FAILED.value
        execution.error_message = str(error)[:1000]
        execution.completed_at = datetime.utcnow()
        session.commit()
        session.refresh(execution)

        return execution

    @staticmethod
    def increment_retry(session, execution: WorkflowExecution) -> WorkflowExecution:
        execution.retry_count = (execution.retry_count or 0) + 1
        session.commit()
        session.refresh(execution)

        return execution
