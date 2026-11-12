from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.permissions import require_org_role
from app.db.session import get_db
from app.schemas.event import EventPublishRequest, EventPublishResponse
from app.services.event_service import EventService
from app.utils.enums import UserRole

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/publish", response_model=EventPublishResponse, status_code=status.HTTP_202_ACCEPTED
)
async def publish_event(
    payload: EventPublishRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    await require_org_role(db, user_id, payload.organization_id, UserRole.MEMBER)

    return await EventService.publish_event(payload)
