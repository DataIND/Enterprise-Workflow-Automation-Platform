import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMTPClient:

    @staticmethod
    def send(email: str, subject: str, message: str) -> bool:
        """Send an email. Returns False when SMTP is not configured.

        Local development usually has no SMTP server, so an unset SMTP_HOST
        logs the message instead of failing the workflow.
        """

        if not settings.SMTP_HOST:
            logger.info(
                "SMTP not configured, skipping send to=%s subject=%s", email, subject
            )
            return False

        envelope = EmailMessage()
        envelope["From"] = settings.SMTP_FROM
        envelope["To"] = email
        envelope["Subject"] = subject
        envelope.set_content(message)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            smtp.send_message(envelope)

        return True
