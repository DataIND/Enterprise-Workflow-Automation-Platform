"""Bridges worker processes to the API's WebSocket connections.

Celery workers and the consumer run in separate processes, so they cannot
reach the API's in-memory ConnectionManager. They publish to Redis instead and
the API fans the message out to whichever sockets it holds locally. This also
keeps things correct when the API is scaled to several replicas.
"""

import asyncio
import json
import logging

import redis
import redis.asyncio as redis_async

from app.core.config import settings
from app.services.websocket_service import WebSocketService
from app.websocket.connection_manager import EXECUTIONS_TOPIC

logger = logging.getLogger(__name__)

_sync_client: redis.Redis | None = None


def _client() -> redis.Redis:
    global _sync_client

    if _sync_client is None:
        _sync_client = redis.Redis.from_url(settings.REDIS_URL)

    return _sync_client


def publish_event(message: dict) -> None:
    """Called from worker processes. Never raises into the caller."""

    try:
        _client().publish(settings.EXECUTION_EVENTS_CHANNEL, json.dumps(message, default=str))
    except Exception:
        logger.warning("Could not publish realtime event to Redis", exc_info=True)


async def run_subscriber() -> None:
    """Long-running API task: forward Redis messages to local sockets."""

    client = redis_async.Redis.from_url(settings.REDIS_URL)
    pubsub = client.pubsub()

    await pubsub.subscribe(settings.EXECUTION_EVENTS_CHANNEL)

    try:
        async for raw in pubsub.listen():
            if raw.get("type") != "message":
                continue

            try:
                message = json.loads(raw["data"])
            except (TypeError, ValueError):
                logger.warning("Discarding malformed realtime message")
                continue

            user_ids = message.pop("user_ids", [])
            topic = message.get("topic", EXECUTIONS_TOPIC)

            await WebSocketService.notify_users(user_ids, message, topic=topic)
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.aclose()
        await client.aclose()
