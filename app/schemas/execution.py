from datetime import datetime

from pydantic import BaseModel


class ExecutionResponse(BaseModel):

    id: int

    workflow_id: int

    event_id: str | None

    status: str

    error_message: str | None

    retry_count: int

    started_at: datetime

    completed_at: datetime | None

    class Config:

        from_attributes = True
