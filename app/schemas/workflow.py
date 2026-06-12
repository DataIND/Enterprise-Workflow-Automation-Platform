from pydantic import BaseModel
from datetime import datetime


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str | None
    trigger_type: str
    is_active: bool
    created_at: datetime

    class Config:

        from_attributes = True
