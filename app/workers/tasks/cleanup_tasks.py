import logging
from datetime import datetime, timedelta

from sqlalchemy import delete

from app.core.config import settings
from app.db.models.workflow_execution import WorkflowExecution
from app.db.sync_session import session_scope
from app.utils.enums import WorkflowStatus
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = (WorkflowStatus.SUCCESS.value, WorkflowStatus.FAILED.value)


@celery_app.task(name="app.workers.tasks.cleanup_tasks.cleanup_old_logs")
def cleanup_old_logs(retention_days: int | None = None):
    """Delete finished executions older than the retention window."""

    days = retention_days or settings.EXECUTION_RETENTION_DAYS
    cutoff = datetime.utcnow() - timedelta(days=days)

    with session_scope() as session:
        result = session.execute(
            delete(WorkflowExecution).where(
                WorkflowExecution.status.in_(TERMINAL_STATUSES),
                WorkflowExecution.started_at < cutoff,
            )
        )
        session.commit()

    deleted = result.rowcount or 0

    logger.info("Cleaned up %s executions older than %s days", deleted, days)

    return {"deleted": deleted, "cutoff": cutoff.isoformat()}
