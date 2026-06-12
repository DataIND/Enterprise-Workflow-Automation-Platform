from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, JSON, DateTime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowAction(Base):

    __tablename__ = "workflow_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE")
    )

    action_type: Mapped[str] = mapped_column(String(100))

    config: Mapped[dict] = mapped_column(JSON)

    execution_order: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="actions")
