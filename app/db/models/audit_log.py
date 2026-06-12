from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, JSON

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    action: Mapped[str] = mapped_column(String(100))

    entity_type: Mapped[str] = mapped_column(String(100))

    entity_id: Mapped[int]

    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
