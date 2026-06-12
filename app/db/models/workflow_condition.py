from datetime import datetime


from sqlalchemy import ForeignKey, String, JSON, DateTime


from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.base import Base


class WorkflowCondition(Base):

    __tablename__ = "workflow_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE")
    )

    field: Mapped[str] = mapped_column(String(100))

    operator: Mapped[str] = mapped_column(String(50))

    value: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="conditions")
