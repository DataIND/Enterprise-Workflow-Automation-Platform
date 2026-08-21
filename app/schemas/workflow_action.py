from typing import Any, Dict

from pydantic import BaseModel

from app.utils.enums import ActionType


class WorkflowActionCreate(BaseModel):

    action_type: ActionType

    config: Dict[str, Any]

    execution_order: int = 1


class WorkflowActionUpdate(BaseModel):

    action_type: ActionType | None = None

    config: Dict[str, Any] | None = None

    execution_order: int | None = None


class WorkflowActionResponse(BaseModel):

    id: int

    workflow_id: int

    action_type: str

    config: dict

    execution_order: int

    class Config:

        from_attributes = True
