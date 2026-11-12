"""Single source of truth for the RabbitMQ exchange/queue layout.

Both the publisher and the consumer declare the topology on startup so the
layout exists regardless of which process comes up first.
"""

from app.core.config import settings

EVENT_ROUTING_KEY = "workflow.event"


def declare_topology(channel) -> None:
    """Declare exchanges, queues and bindings on a blocking pika channel."""

    channel.exchange_declare(
        exchange=settings.EVENT_EXCHANGE,
        exchange_type="direct",
        durable=True,
    )

    channel.exchange_declare(
        exchange=settings.DEAD_LETTER_EXCHANGE,
        exchange_type="direct",
        durable=True,
    )

    channel.queue_declare(
        queue=settings.DEAD_LETTER_QUEUE,
        durable=True,
    )

    channel.queue_bind(
        queue=settings.DEAD_LETTER_QUEUE,
        exchange=settings.DEAD_LETTER_EXCHANGE,
        routing_key=settings.DEAD_LETTER_QUEUE,
    )

    # Rejected events are routed to the dead letter exchange instead of being
    # dropped or redelivered forever.
    channel.queue_declare(
        queue=settings.EVENT_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.DEAD_LETTER_EXCHANGE,
            "x-dead-letter-routing-key": settings.DEAD_LETTER_QUEUE,
        },
    )

    channel.queue_bind(
        queue=settings.EVENT_QUEUE,
        exchange=settings.EVENT_EXCHANGE,
        routing_key=EVENT_ROUTING_KEY,
    )

    # Celery action queues. Declared durable to match Celery's own defaults.
    for queue in (settings.EMAIL_QUEUE, settings.WEBHOOK_QUEUE, settings.RETRY_QUEUE):
        channel.queue_declare(queue=queue, durable=True)
