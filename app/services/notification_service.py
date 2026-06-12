from app.db.models.notification import Notification

from app.repositories.notification_repository import NotificationRepository

repo = NotificationRepository()


class NotificationService:

    async def create(self, db, user_id, title, message):

        notification = Notification(user_id=user_id, title=title, message=message)

        return await repo.create(db, notification)

    async def list(self, db, user_id):

        return await repo.get_user_notifications(db, user_id)
