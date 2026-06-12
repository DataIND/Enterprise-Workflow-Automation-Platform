from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.connections = {}

    async def connect(self, user_id: int, websocket: WebSocket):

        await websocket.accept()

        self.connections[user_id] = websocket

    def disconnect(self, user_id):

        self.connections.pop(user_id, None)

    async def send(self, user_id, message):

        websocket = self.connections.get(user_id)

        if websocket:

            await websocket.send_json(message)


manager = ConnectionManager()
