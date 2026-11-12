from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    RABBITMQ_URL: str

    # Event bus topology
    EVENT_EXCHANGE: str = "workflow.events"
    DEAD_LETTER_EXCHANGE: str = "workflow.dlx"
    EVENT_QUEUE: str = "event_queue"
    EMAIL_QUEUE: str = "email_queue"
    WEBHOOK_QUEUE: str = "webhook_queue"
    RETRY_QUEUE: str = "retry_queue"
    DEAD_LETTER_QUEUE: str = "dead_letter_queue"

    # Execution behaviour
    MAX_ACTION_RETRIES: int = 5
    ACTION_RETRY_BACKOFF_MAX: int = 600
    EXECUTION_RETENTION_DAYS: int = 30

    # Real-time bridge
    EXECUTION_EVENTS_CHANNEL: str = "workflow:execution_events"

    # Email delivery. Without SMTP_HOST the client logs instead of sending.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@workflow.local"
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Workers and the consumer are synchronous, so drop the async driver."""

        return self.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")


settings = Settings()
