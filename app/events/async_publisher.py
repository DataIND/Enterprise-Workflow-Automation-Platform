"""Async RabbitMQ publisher for the request path.

The API runs on an event loop, so it cannot use the blocking pika client
without stalling every other request. One robust connection is opened during
application startup and reused for all publishes.
"""

import json
import logging

import aio_pika

from app.core.config import settings
from app.events.topology import EVENT_ROUTING_KEY

logger = logging.getLogger(__name__)


class AsyncEventPublisher:
    _connection: aio_pika.abc.AbstractRobustConnection | None = None
    _channel: aio_pika.abc.AbstractRobustChannel | None = None
    _exchange: aio_pika.abc.AbstractExchange | None = None

    @classmethod
    async def connect(cls) -> None:
        if cls._connection is not None and not cls._connection.is_closed:
            return

        cls._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        cls._channel = await cls._connection.channel()
        cls._exchange = await cls._channel.declare_exchange(
            settings.EVENT_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        dlx = await cls._channel.declare_exchange(
            settings.DEAD_LETTER_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        dead_letter_queue = await cls._channel.declare_queue(
            settings.DEAD_LETTER_QUEUE, durable=True
        )
        await dead_letter_queue.bind(dlx, routing_key=settings.DEAD_LETTER_QUEUE)

        event_queue = await cls._channel.declare_queue(
            settings.EVENT_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.DEAD_LETTER_EXCHANGE,
                "x-dead-letter-routing-key": settings.DEAD_LETTER_QUEUE,
            },
        )
        await event_queue.bind(cls._exchange, routing_key=EVENT_ROUTING_KEY)

    @classmethod
    async def close(cls) -> None:
        if cls._connection is not None and not cls._connection.is_closed:
            await cls._connection.close()

        cls._connection = None
        cls._channel = None
        cls._exchange = None

    @classmethod
    async def publish(cls, message: dict, routing_key: str = EVENT_ROUTING_KEY) -> None:
        if cls._exchange is None or cls._connection is None or cls._connection.is_closed:
            await cls.connect()

        await cls._exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message.get("event_id"),
            ),
            routing_key=routing_key,
        )
