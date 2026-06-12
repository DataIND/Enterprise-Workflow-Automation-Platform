from fastapi import APIRouter


from app.schemas.event import EventPublishRequest


from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/publish")
async def publish_event(payload: EventPublishRequest):

    return await EventService.publish_event(payload)
