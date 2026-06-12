from datetime import datetime


from sqlalchemy import ForeignKey, String, DateTime, JSON


from sqlalchemy.orm import Mapped, mapped_column


from app.db.base import Base


class WorkflowExecution(Base):

    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"))

    status: Mapped[str] = mapped_column(String(50), default="PENDING")

    event_payload: Mapped[dict] = mapped_column(JSON)

    error_message: Mapped[str | None]

    retry_count: Mapped[int] = mapped_column(default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    completed_at: Mapped[datetime | None]
