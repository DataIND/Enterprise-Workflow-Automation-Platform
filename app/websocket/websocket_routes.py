from fastapi import APIRouter, WebSocket


from app.websocket.connection_manager import manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):

    await manager.connect(user_id, websocket)

    try:

        while True:

            await websocket.receive_text()

    except Exception:

        manager.disconnect(user_id)
