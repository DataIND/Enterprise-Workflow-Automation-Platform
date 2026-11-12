from app.core.config import settings
from app.integrations.email.smtp_client import SMTPClient
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.email_tasks.send_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=settings.ACTION_RETRY_BACKOFF_MAX,
    retry_jitter=True,
    max_retries=settings.MAX_ACTION_RETRIES,
)
def send_email(self, email: str, subject: str, message: str):
    sent = SMTPClient.send(email, subject, message)

    return "EMAIL_SENT" if sent else "EMAIL_SKIPPED"
