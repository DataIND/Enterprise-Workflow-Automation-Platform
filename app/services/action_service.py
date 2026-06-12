from app.db.models.workflow_action import WorkflowAction


from app.repositories.workflow_action_repository import WorkflowActionRepository

repo = WorkflowActionRepository()


class ActionService:

    async def create_action(self, db, workflow_id, payload):

        action = WorkflowAction(
            workflow_id=workflow_id,
            action_type=payload.action_type,
            config=payload.config,
            execution_order=payload.execution_order,
        )

        return await repo.create(db, action)
