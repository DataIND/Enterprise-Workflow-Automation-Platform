from datetime import datetime

from pydantic import BaseModel


class ExecutionResponse(BaseModel):

    id: int

    workflow_id: int

    status: str

    retry_count: int

    started_at: datetime

    class Config:

        from_attributes = True
