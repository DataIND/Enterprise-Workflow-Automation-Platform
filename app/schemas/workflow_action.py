from typing import Dict, Any

from pydantic import BaseModel


class WorkflowActionCreate(BaseModel):

    action_type: str

    config: Dict[str, Any]

    execution_order: int = 1


class WorkflowActionResponse(BaseModel):

    id: int

    workflow_id: int

    action_type: str

    config: dict

    execution_order: int

    class Config:

        from_attributes = True
