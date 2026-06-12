from datetime import datetime


from sqlalchemy import ForeignKey, String, Boolean, DateTime


from sqlalchemy.orm import Mapped, mapped_column


from app.db.base import Base


class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(255))

    message: Mapped[str]

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
