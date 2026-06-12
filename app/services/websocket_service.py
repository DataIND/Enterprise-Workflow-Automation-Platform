from app.websocket.connection_manager import manager


class WebSocketService:

    @staticmethod
    async def notify_user(user_id, message):

        await manager.send(user_id, message)
