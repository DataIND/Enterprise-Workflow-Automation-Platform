from app.core.config import settings
from app.integrations.webhook.webhook_client import WebhookClient
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.webhook_tasks.send_webhook",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=settings.ACTION_RETRY_BACKOFF_MAX,
    retry_jitter=True,
    max_retries=settings.MAX_ACTION_RETRIES,
)
def send_webhook(self, url: str, payload: dict):
    response = WebhookClient.post(url, payload)
    response.raise_for_status()

    return response.status_code
