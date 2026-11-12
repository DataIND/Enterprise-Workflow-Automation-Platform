from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "workflow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.workflow_tasks",
        "app.workers.tasks.email_tasks",
        "app.workers.tasks.webhook_tasks",
        "app.workers.tasks.cleanup_tasks",
    ],
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.email_tasks.*": {"queue": settings.EMAIL_QUEUE},
        "app.workers.tasks.webhook_tasks.*": {"queue": settings.WEBHOOK_QUEUE},
        "app.workers.tasks.workflow_tasks.retry_execution": {
            "queue": settings.RETRY_QUEUE
        },
    },
    beat_schedule={
        "cleanup-old-executions": {
            "task": "app.workers.tasks.cleanup_tasks.cleanup_old_logs",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
