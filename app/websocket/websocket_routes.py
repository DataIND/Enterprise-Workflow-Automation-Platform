from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.websocket.connection_manager import (
    EXECUTIONS_TOPIC,
    NOTIFICATIONS_TOPIC,
    manager,
)

router = APIRouter()


async def _authenticate(token: str | None) -> int | None:
    """Resolve a user id from a JWT handed over as a query parameter.

    Browsers cannot set Authorization headers on a WebSocket handshake, so the
    access token is passed as ?token=.
    """

    if not token:
        return None

    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user.id


async def _serve(websocket: WebSocket, topic: str, token: str | None) -> None:
    user_id = await _authenticate(token)

    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(topic, user_id, websocket)

    try:
        while True:
            # The channel is server-push only; this keeps the socket open and
            # surfaces client disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(topic, user_id, websocket)


@router.websocket("/ws/executions")
async def executions_socket(websocket: WebSocket, token: str | None = Query(default=None)):
    await _serve(websocket, EXECUTIONS_TOPIC, token)


@router.websocket("/ws/notifications")
async def notifications_socket(
    websocket: WebSocket, token: str | None = Query(default=None)
):
    await _serve(websocket, NOTIFICATIONS_TOPIC, token)
