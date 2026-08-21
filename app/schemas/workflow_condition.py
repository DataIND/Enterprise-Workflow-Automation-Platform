from typing import Any

from pydantic import BaseModel

from app.utils.enums import ConditionOperator


class WorkflowConditionCreate(BaseModel):

    field: str

    operator: ConditionOperator

    value: Any


class WorkflowConditionUpdate(BaseModel):

    field: str | None = None

    operator: ConditionOperator | None = None

    value: Any = None


class WorkflowConditionResponse(BaseModel):

    id: int

    workflow_id: int

    field: str

    operator: str

    value: Any

    class Config:

        from_attributes = True
