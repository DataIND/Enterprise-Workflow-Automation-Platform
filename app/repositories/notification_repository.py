from sqlalchemy import select

from app.db.models.notification import Notification


class NotificationRepository:

    async def create(self, db, notification):

        db.add(notification)

        await db.commit()

        await db.refresh(notification)

        return notification

    async def get_user_notifications(self, db, user_id):

        result = await db.execute(
            select(Notification).where(Notification.user_id == user_id)
        )

        return result.scalars().all()
