import uuid
from datetime import datetime

from app.events.async_publisher import AsyncEventPublisher


class EventService:

    @staticmethod
    def build_envelope(payload) -> dict:
        return {
            "event_id": payload.event_id or str(uuid.uuid4()),
            "event_type": payload.event_type,
            "organization_id": payload.organization_id,
            "payload": payload.payload,
            "published_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def publish_event(payload) -> dict:
        envelope = EventService.build_envelope(payload)

        await AsyncEventPublisher.publish(envelope)

        return envelope
