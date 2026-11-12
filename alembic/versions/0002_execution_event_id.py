"""add event_id idempotency key to workflow_executions

Revision ID: 0002_execution_event_id
Revises: 0001_initial
Create Date: 2026-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_execution_event_id"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflow_executions",
        sa.Column("event_id", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_workflow_executions_event_id", "workflow_executions", ["event_id"]
    )
    op.create_unique_constraint(
        "uq_execution_workflow_event",
        "workflow_executions",
        ["workflow_id", "event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_execution_workflow_event", "workflow_executions", type_="unique"
    )
    op.drop_index("ix_workflow_executions_event_id", table_name="workflow_executions")
    op.drop_column("workflow_executions", "event_id")
