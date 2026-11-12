from app.websocket.connection_manager import manager


class WebSocketService:

    @staticmethod
    async def notify_user(user_id: int, message: dict, topic: str | None = None) -> int:
        return await manager.send(user_id, message, topic=topic)

    @staticmethod
    async def notify_users(
        user_ids, message: dict, topic: str | None = None
    ) -> int:
        delivered = 0

        for user_id in user_ids:
            delivered += await WebSocketService.notify_user(user_id, message, topic)

        return delivered
