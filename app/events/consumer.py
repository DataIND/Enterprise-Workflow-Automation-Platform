"""RabbitMQ consumer: turns published events into workflow executions.

Run as its own process:

    python -m app.events.consumer
"""

import logging
import signal
import time

import pika
from pika.exceptions import AMQPConnectionError, AMQPError

from app.core.config import settings
from app.db.sync_session import session_scope
from app.engine.event_handler import handle_event, parse_envelope
from app.events.topology import declare_topology

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger("app.events.consumer")

RECONNECT_DELAY_SECONDS = 5

_shutdown = False


def _request_shutdown(signum, frame):
    global _shutdown
    _shutdown = True
    logger.info("Shutdown signal received, finishing current message")


def on_message(channel, method, properties, body) -> None:
    delivery_tag = method.delivery_tag

    try:
        envelope = parse_envelope(body)
    except ValueError as exc:
        # Malformed messages can never succeed, so send them straight to the DLQ.
        logger.error("Dead-lettering malformed event: %s", exc)
        channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
        return

    try:
        with session_scope() as session:
            execution_ids = handle_event(session, envelope)

        logger.info(
            "Handled event_id=%s event_type=%s executions=%s",
            envelope.get("event_id"),
            envelope.get("event_type"),
            execution_ids,
        )

        channel.basic_ack(delivery_tag=delivery_tag)
    except Exception:
        # Give a transient failure (database blip, broker hiccup) exactly one
        # more attempt before dead-lettering it.
        requeue = not method.redelivered

        logger.exception(
            "Failed to handle event_id=%s, requeue=%s",
            envelope.get("event_id"),
            requeue,
        )

        channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)


def consume_once() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))

    try:
        channel = connection.channel()

        declare_topology(channel)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=settings.EVENT_QUEUE,
            on_message_callback=on_message,
        )

        logger.info("Consuming from %s", settings.EVENT_QUEUE)

        while not _shutdown:
            connection.process_data_events(time_limit=1)

        channel.stop_consuming()
    finally:
        if connection.is_open:
            connection.close()


def run() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    while not _shutdown:
        try:
            consume_once()
        except (AMQPConnectionError, AMQPError):
            if _shutdown:
                break

            logger.warning(
                "Broker unavailable, reconnecting in %ss", RECONNECT_DELAY_SECONDS
            )
            time.sleep(RECONNECT_DELAY_SECONDS)

    logger.info("Consumer stopped")


if __name__ == "__main__":
    run()
