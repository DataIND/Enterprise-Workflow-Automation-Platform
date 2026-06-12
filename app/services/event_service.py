from app.events.publisher import RabbitMQPublisher


class EventService:

    EVENT_QUEUE = "workflow_events"

    @staticmethod
    async def publish_event(payload):

        event_data = {
            "event_type": payload.event_type,
            "organization_id": payload.organization_id,
            "payload": payload.payload,
        }

        RabbitMQPublisher.publish(queue=EventService.EVENT_QUEUE, message=event_data)

        return {"message": "Event published"}
