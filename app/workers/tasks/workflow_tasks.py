"""Workflow execution tasks.

An execution runs as an ordered Celery chain: one task per action, routed to
the queue for its action type, finished by ``complete_execution``. A chain
stops at the first permanent failure, so a failed action prevents the ones
after it from running.
"""

import logging

from celery import chain

from app.core.config import settings
from app.db.models.workflow import Workflow
from app.db.models.workflow_action import WorkflowAction
from app.db.sync_session import session_scope
from app.engine.actions import (
    ActionContext,
    load_ordered_actions,
    queue_for,
    run_action,
)
from app.engine.realtime import emit_execution_event
from app.events.publisher import RabbitMQPublisher
from app.services.execution_service import ExecutionService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _organization_id(session, workflow_id: int) -> int | None:
    workflow = session.get(Workflow, workflow_id)

    return workflow.organization_id if workflow else None


def _finalize_failure(execution_id: int, exc: Exception) -> None:
    """Mark the execution failed, emit it, and dead-letter the envelope."""

    with session_scope() as session:
        execution = ExecutionService.get(session, execution_id)

        if execution is None:
            return

        ExecutionService.mark_failed(session, execution, exc)

        organization_id = _organization_id(session, execution.workflow_id)

        if organization_id is not None:
            emit_execution_event(session, execution, organization_id)

        envelope = {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "organization_id": organization_id,
            "event_id": execution.event_id,
            "event_payload": execution.event_payload,
            "error": str(exc),
            "retry_count": execution.retry_count,
        }

    try:
        RabbitMQPublisher.publish_dead_letter(envelope)
    except Exception:
        logger.exception("Could not publish execution %s to the DLQ", execution_id)


class ActionTask(celery_app.Task):
    """Base task that records a permanent action failure on the execution.

    ``on_failure`` fires only once retries are exhausted, which is exactly
    when the execution should be marked FAILED and dead-lettered.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        execution_id = kwargs.get("execution_id") or (args[0] if args else None)

        if execution_id is not None:
            _finalize_failure(execution_id, exc)


@celery_app.task(bind=True, name="app.workers.tasks.workflow_tasks.execute_workflow")
def execute_workflow(self, execution_id: int):
    """Expand an execution into a chain of action tasks."""

    with session_scope() as session:
        execution = ExecutionService.get(session, execution_id)

        if execution is None:
            logger.warning("Execution %s no longer exists", execution_id)
            return {"status": "MISSING", "execution_id": execution_id}

        organization_id = _organization_id(session, execution.workflow_id)
        actions = load_ordered_actions(session, execution.workflow_id)

        ExecutionService.mark_running(session, execution)

        if organization_id is not None:
            emit_execution_event(session, execution, organization_id)

        if not actions:
            ExecutionService.mark_success(session, execution)

            if organization_id is not None:
                emit_execution_event(session, execution, organization_id)

            return {"status": execution.status, "actions": 0}

        signatures = [
            run_action_task.si(execution_id, action.id).set(
                queue=queue_for(action.action_type)
            )
            for action in actions
        ]

    signatures.append(complete_execution.si(execution_id))

    chain(*signatures).apply_async()

    return {"status": "DISPATCHED", "actions": len(signatures) - 1}


@celery_app.task(
    bind=True,
    base=ActionTask,
    name="app.workers.tasks.workflow_tasks.run_action_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=settings.ACTION_RETRY_BACKOFF_MAX,
    retry_jitter=True,
    max_retries=settings.MAX_ACTION_RETRIES,
)
def run_action_task(self, execution_id: int, action_id: int):
    with session_scope() as session:
        execution = ExecutionService.get(session, execution_id)
        action = session.get(WorkflowAction, action_id)

        if execution is None or action is None:
            logger.warning(
                "Skipping action %s for execution %s: record missing",
                action_id,
                execution_id,
            )
            return {"status": "SKIPPED"}

        if self.request.retries:
            ExecutionService.increment_retry(session, execution)

        organization_id = _organization_id(session, execution.workflow_id)

        context = ActionContext(
            session=session,
            organization_id=organization_id,
            workflow_id=execution.workflow_id,
            execution_id=execution.id,
            payload=execution.event_payload or {},
        )

        return run_action(action, context)


@celery_app.task(name="app.workers.tasks.workflow_tasks.complete_execution")
def complete_execution(execution_id: int):
    with session_scope() as session:
        execution = ExecutionService.get(session, execution_id)

        if execution is None:
            return {"status": "MISSING"}

        ExecutionService.mark_success(session, execution)

        organization_id = _organization_id(session, execution.workflow_id)

        if organization_id is not None:
            emit_execution_event(session, execution, organization_id)

        return {"status": execution.status, "execution_id": execution.id}


@celery_app.task(name="app.workers.tasks.workflow_tasks.retry_execution")
def retry_execution(execution_id: int):
    """Re-run a failed execution. Routed to the retry queue."""

    with session_scope() as session:
        execution = ExecutionService.get(session, execution_id)

        if execution is None:
            return {"status": "MISSING"}

        ExecutionService.increment_retry(session, execution)

    execute_workflow.delay(execution_id)

    return {"status": "REQUEUED", "execution_id": execution_id}
