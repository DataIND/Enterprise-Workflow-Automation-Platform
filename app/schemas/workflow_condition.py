from typing import Any

from pydantic import BaseModel


class WorkflowConditionCreate(BaseModel):

    field: str

    operator: str

    value: Any


class WorkflowConditionResponse(BaseModel):

    id: int

    workflow_id: int

    field: str

    operator: str

    value: Any

    class Config:

        from_attributes = True
