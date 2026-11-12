from sqlalchemy import select

from app.db.models.workflow import Workflow
from app.db.models.workflow_execution import WorkflowExecution


class ExecutionRepository:
    """Async read/write access used by the API.

    Worker-side writes go through
    :class:`app.services.execution_service.ExecutionService`, which is sync.
    """

    @staticmethod
    async def create(db, execution):
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    @staticmethod
    async def get_by_id(db, execution_id: int):
        result = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_organization_id(db, execution: WorkflowExecution) -> int | None:
        result = await db.execute(
            select(Workflow.organization_id).where(Workflow.id == execution.workflow_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_organization(
        db,
        organization_id: int,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ):
        query = (
            select(WorkflowExecution)
            .join(Workflow, Workflow.id == WorkflowExecution.workflow_id)
            .where(Workflow.organization_id == organization_id)
            .order_by(WorkflowExecution.started_at.desc(), WorkflowExecution.id.desc())
        )

        if status:
            query = query.where(WorkflowExecution.status == status)

        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)

        return result.scalars().all()
