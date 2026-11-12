from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class EventPublishRequest(BaseModel):

    event_type: str

    organization_id: int

    payload: Dict[str, Any]

    # Supplying the same event_id twice is a no-op: the engine will not run a
    # workflow more than once for a given event.
    event_id: str | None = None


class EventPublishResponse(BaseModel):

    event_id: str

    event_type: str

    organization_id: int

    published_at: datetime
