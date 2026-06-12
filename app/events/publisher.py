import pika
import json


from app.core.config import settings


class RabbitMQPublisher:

    @staticmethod
    def publish(queue: str, message: dict):

        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))

        channel = connection.channel()

        channel.queue_declare(queue=queue, durable=True)

        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )

        connection.close()
