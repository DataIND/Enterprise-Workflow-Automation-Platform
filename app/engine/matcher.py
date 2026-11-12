"""Decides which workflows should run for an incoming event."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.membership import Membership
from app.db.models.workflow import Workflow
from app.services.condition_service import ConditionService


def find_matching_workflows(
    session, organization_id: int, trigger_type: str, payload: dict
) -> list[Workflow]:
    """Active workflows in the org whose trigger and conditions both match."""

    workflows = (
        session.execute(
            select(Workflow)
            .options(selectinload(Workflow.conditions))
            .where(
                Workflow.organization_id == organization_id,
                Workflow.trigger_type == trigger_type,
                Workflow.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )

    return [
        workflow
        for workflow in workflows
        if ConditionService.validate(workflow.conditions, payload)
    ]


def organization_member_ids(session, organization_id: int) -> list[int]:
    return list(
        session.execute(
            select(Membership.user_id).where(
                Membership.organization_id == organization_id
            )
        )
        .scalars()
        .all()
    )
