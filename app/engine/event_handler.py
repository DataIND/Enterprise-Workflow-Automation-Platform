"""Turns an incoming event into workflow executions.

Shared by the RabbitMQ consumer and the test suite, so it takes a plain
session and an already-decoded envelope.
"""

import json
import logging

from app.engine.matcher import find_matching_workflows
from app.engine.realtime import emit_execution_event
from app.services.execution_service import ExecutionService

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ("event_type", "organization_id", "payload")


def parse_envelope(body) -> dict:
    """Decode and validate a message body. Raises ValueError when malformed."""

    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8")

    if isinstance(body, str):
        try:
            body = json.loads(body)
        except ValueError as exc:
            raise ValueError(f"Event body is not valid JSON: {exc}") from exc

    if not isinstance(body, dict):
        raise ValueError("Event body must be a JSON object")

    missing = [field for field in REQUIRED_FIELDS if body.get(field) is None]

    if missing:
        raise ValueError(f"Event is missing required fields: {', '.join(missing)}")

    if not isinstance(body["payload"], dict):
        raise ValueError("Event payload must be a JSON object")

    return body


def _default_dispatch(execution_id: int) -> None:
    from app.workers.tasks.workflow_tasks import execute_workflow

    execute_workflow.delay(execution_id)


def handle_event(session, envelope: dict, dispatch=None) -> list[int]:
    """Match the event to workflows and queue an execution for each.

    Returns the execution ids that were dispatched. Duplicates (same event_id
    for the same workflow) are skipped.
    """

    dispatch = dispatch or _default_dispatch

    organization_id = int(envelope["organization_id"])
    event_type = envelope["event_type"]
    payload = envelope["payload"]
    event_id = envelope.get("event_id")

    workflows = find_matching_workflows(session, organization_id, event_type, payload)

    if not workflows:
        logger.info(
            "No workflow matched event_type=%s organization_id=%s",
            event_type,
            organization_id,
        )
        return []

    dispatched: list[int] = []

    for workflow in workflows:
        execution = ExecutionService.start_execution(
            session,
            workflow_id=workflow.id,
            event_payload=payload,
            event_id=event_id,
        )

        if execution is None:
            logger.info(
                "Skipping duplicate event_id=%s for workflow_id=%s",
                event_id,
                workflow.id,
            )
            continue

        emit_execution_event(session, execution, organization_id)

        dispatch(execution.id)
        dispatched.append(execution.id)

    return dispatched
