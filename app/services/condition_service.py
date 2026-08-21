from fastapi import HTTPException, status

from app.db.models.workflow_condition import WorkflowCondition
from app.repositories.workflow_condition_repository import WorkflowConditionRepository
from app.utils.enums import ConditionOperator

_MISSING = object()


class ConditionService:

    @staticmethod
    async def create_condition(db, workflow_id: int, payload):
        condition = WorkflowCondition(
            workflow_id=workflow_id,
            field=payload.field,
            operator=payload.operator.value,
            value=payload.value,
        )

        return await WorkflowConditionRepository.create(db, condition)

    @staticmethod
    async def list_conditions(db, workflow_id: int):
        return await WorkflowConditionRepository.get_by_workflow(db, workflow_id)

    @staticmethod
    async def get_condition(
        db, workflow_id: int, condition_id: int
    ) -> WorkflowCondition:
        condition = await WorkflowConditionRepository.get_by_id(db, condition_id)

        if not condition or condition.workflow_id != workflow_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Condition not found",
            )

        return condition

    @staticmethod
    async def update_condition(db, workflow_id: int, condition_id: int, payload):
        condition = await ConditionService.get_condition(db, workflow_id, condition_id)

        update_data = payload.model_dump(exclude_unset=True, mode="json")

        for key, value in update_data.items():
            setattr(condition, key, value)

        await db.commit()
        await db.refresh(condition)

        return condition

    @staticmethod
    async def delete_condition(db, workflow_id: int, condition_id: int):
        condition = await ConditionService.get_condition(db, workflow_id, condition_id)

        await WorkflowConditionRepository.delete(db, condition)

        return {"message": "Condition deleted"}

    @staticmethod
    def validate(conditions, payload: dict) -> bool:
        """Return True when every condition matches the event payload."""

        for condition in conditions:
            actual = payload.get(condition.field, _MISSING)

            if actual is _MISSING:
                return False

            if not ConditionService._matches(
                condition.operator, actual, condition.value
            ):
                return False

        return True

    @staticmethod
    def _matches(operator: str, actual, expected) -> bool:
        try:
            if operator == ConditionOperator.EQ:
                return actual == expected

            if operator == ConditionOperator.NE:
                return actual != expected

            if operator == ConditionOperator.GT:
                return actual > expected

            if operator == ConditionOperator.GTE:
                return actual >= expected

            if operator == ConditionOperator.LT:
                return actual < expected

            if operator == ConditionOperator.LTE:
                return actual <= expected

            if operator == ConditionOperator.CONTAINS:
                return expected in actual

            if operator == ConditionOperator.IN:
                return actual in expected
        except TypeError:
            return False

        return False
