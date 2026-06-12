from pydantic import BaseModel

from typing import Dict, Any


class EventPublishRequest(BaseModel):

    event_type: str

    organization_id: int

    payload: Dict[str, Any]
