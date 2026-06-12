from app.workers.celery_app import celery_app

from app.integrations.email.smtp_client import SMTPClient


@celery_app.task(bind=True, max_retries=3)
def send_email(self, email, subject, message):

    try:

        SMTPClient.send(email, subject, message)

        return "EMAIL_SENT"

    except Exception as exc:

        raise self.retry(exc=exc, countdown=10)
