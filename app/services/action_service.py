from fastapi import HTTPException, status

from app.db.models.workflow_action import WorkflowAction
from app.repositories.workflow_action_repository import WorkflowActionRepository


class ActionService:

    @staticmethod
    async def create_action(db, workflow_id: int, payload):
        action = WorkflowAction(
            workflow_id=workflow_id,
            action_type=payload.action_type.value,
            config=payload.config,
            execution_order=payload.execution_order,
        )

        return await WorkflowActionRepository.create(db, action)

    @staticmethod
    async def list_actions(db, workflow_id: int):
        return await WorkflowActionRepository.get_by_workflow(db, workflow_id)

    @staticmethod
    async def get_action(db, workflow_id: int, action_id: int) -> WorkflowAction:
        action = await WorkflowActionRepository.get_by_id(db, action_id)

        if not action or action.workflow_id != workflow_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found",
            )

        return action

    @staticmethod
    async def update_action(db, workflow_id: int, action_id: int, payload):
        action = await ActionService.get_action(db, workflow_id, action_id)

        update_data = payload.model_dump(exclude_unset=True, mode="json")

        for key, value in update_data.items():
            setattr(action, key, value)

        await db.commit()
        await db.refresh(action)

        return action

    @staticmethod
    async def delete_action(db, workflow_id: int, action_id: int):
        action = await ActionService.get_action(db, workflow_id, action_id)

        await WorkflowActionRepository.delete(db, action)

        return {"message": "Action deleted"}
