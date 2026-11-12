from fastapi import WebSocket

EXECUTIONS_TOPIC = "executions"
NOTIFICATIONS_TOPIC = "notifications"


class ConnectionManager:
    """Tracks live sockets per topic per user.

    A user may have several sockets open (multiple tabs), so connections are
    held in a set rather than a single slot.
    """

    def __init__(self):
        self._topics: dict[str, dict[int, set[WebSocket]]] = {}

    async def connect(self, topic: str, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()

        self._topics.setdefault(topic, {}).setdefault(user_id, set()).add(websocket)

    def disconnect(self, topic: str, user_id: int, websocket: WebSocket) -> None:
        sockets = self._topics.get(topic, {}).get(user_id)

        if not sockets:
            return

        sockets.discard(websocket)

        if not sockets:
            self._topics[topic].pop(user_id, None)

    def connection_count(self, topic: str, user_id: int) -> int:
        return len(self._topics.get(topic, {}).get(user_id, ()))

    async def send(self, user_id: int, message: dict, topic: str | None = None) -> int:
        topics = [topic] if topic else list(self._topics.keys())

        delivered = 0
        broken: list[tuple[str, WebSocket]] = []

        for name in topics:
            for websocket in set(self._topics.get(name, {}).get(user_id, ())):
                try:
                    await websocket.send_json(message)
                    delivered += 1
                except Exception:
                    broken.append((name, websocket))

        for name, websocket in broken:
            self.disconnect(name, user_id, websocket)

        return delivered


manager = ConnectionManager()
