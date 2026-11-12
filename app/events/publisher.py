"""Blocking publisher used by Celery workers and the consumer process.

The API must not use this; it publishes through
:class:`app.events.async_publisher.AsyncEventPublisher` instead.
"""

import json

import pika

from app.core.config import settings
from app.events.topology import declare_topology


class RabbitMQPublisher:

    @staticmethod
    def publish(
        message: dict,
        exchange: str = "",
        routing_key: str | None = None,
        queue: str | None = None,
    ) -> None:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))

        try:
            channel = connection.channel()
            declare_topology(channel)

            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key or queue or "",
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="application/json",
                ),
            )
        finally:
            connection.close()

    @staticmethod
    def publish_dead_letter(message: dict) -> None:
        RabbitMQPublisher.publish(
            message,
            exchange=settings.DEAD_LETTER_EXCHANGE,
            routing_key=settings.DEAD_LETTER_QUEUE,
        )
