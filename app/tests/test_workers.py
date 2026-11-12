from datetime import datetime, timedelta

import pytest

from app.db.models.notification import Notification
from app.db.models.workflow_action import WorkflowAction
from app.db.models.workflow_execution import WorkflowExecution
from app.engine.actions import ActionContext, render, run_action
from app.engine.event_handler import handle_event
from app.services.condition_service import ConditionService
from app.services.execution_service import ExecutionService
from app.utils.enums import WorkflowStatus
from app.workers.tasks import workflow_tasks
from app.workers.tasks.cleanup_tasks import cleanup_old_logs


class FakeCondition:
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None


def envelope(org_id, event_id="evt-1", payload=None):
    return {
        "event_id": event_id,
        "event_type": "payment.failed",
        "organization_id": org_id,
        "payload": payload if payload is not None else {"amount": 500},
    }


# ---------------------------------------------------------------- conditions


@pytest.mark.parametrize(
    "operator,expected,actual,matches",
    [
        ("eq", "ok", "ok", True),
        ("eq", "ok", "no", False),
        ("ne", "ok", "no", True),
        ("gt", 10, 20, True),
        ("gt", 10, 5, False),
        ("gte", 10, 10, True),
        ("lt", 10, 5, True),
        ("lte", 10, 10, True),
        ("contains", "fail", "payment failed", True),
        ("contains", "zzz", "payment failed", False),
        ("in", ["a", "b"], "a", True),
        ("in", ["a", "b"], "z", False),
    ],
)
def test_condition_operators(operator, expected, actual, matches):
    condition = FakeCondition("field", operator, expected)

    assert ConditionService.validate([condition], {"field": actual}) is matches


def test_condition_missing_field_does_not_match():
    assert ConditionService.validate([FakeCondition("x", "eq", 1)], {}) is False


def test_condition_type_mismatch_is_safe():
    assert ConditionService.validate([FakeCondition("n", "gt", 5)], {"n": None}) is False


def test_all_conditions_must_pass():
    conditions = [FakeCondition("a", "eq", 1), FakeCondition("b", "eq", 2)]

    assert ConditionService.validate(conditions, {"a": 1, "b": 3}) is False
    assert ConditionService.validate(conditions, {"a": 1, "b": 2}) is True


# ---------------------------------------------------------------- templating


def test_render_substitutes_payload_values():
    assert render("Order {id} failed", {"id": 7}) == "Order 7 failed"


def test_render_leaves_unknown_placeholders_intact():
    assert render("Hello {missing}", {}) == "Hello {missing}"


def test_render_passes_through_non_strings():
    assert render({"a": 1}, {}) == {"a": 1}


# ---------------------------------------------------------------- action handlers


def _context(session, payload=None):
    return ActionContext(
        session=session,
        organization_id=1,
        workflow_id=1,
        execution_id=1,
        payload=(
            payload
            if payload is not None
            else {"amount": 500, "email": "fallback@x.com"}
        ),
    )


def test_email_action_uses_config_recipient(session, monkeypatch):
    sent = {}

    monkeypatch.setattr(
        "app.engine.actions.SMTPClient.send",
        lambda email, subject, message: sent.update(
            {"email": email, "subject": subject, "message": message}
        )
        or True,
    )

    action = WorkflowAction(
        action_type="EMAIL",
        config={"to": "ops@x.com", "subject": "Amount {amount}", "body": "hi"},
    )

    result = run_action(action, _context(session))

    assert result["sent"] is True
    assert sent["email"] == "ops@x.com"
    assert sent["subject"] == "Amount 500"


def test_email_action_falls_back_to_payload_email(session, monkeypatch):
    monkeypatch.setattr(
        "app.engine.actions.SMTPClient.send", lambda *a, **k: True
    )

    action = WorkflowAction(action_type="EMAIL", config={})

    assert run_action(action, _context(session))["to"] == "fallback@x.com"


def test_email_action_without_recipient_raises(session):
    action = WorkflowAction(action_type="EMAIL", config={})

    with pytest.raises(ValueError):
        run_action(action, _context(session, payload={}))


def test_webhook_action_posts(session, monkeypatch):
    calls = {}

    monkeypatch.setattr(
        "app.engine.actions.WebhookClient.post",
        lambda url, payload: calls.update({"url": url, "payload": payload})
        or FakeResponse(),
    )

    action = WorkflowAction(action_type="WEBHOOK", config={"url": "https://x.com/h"})

    assert run_action(action, _context(session))["status"] == 200
    assert calls["url"] == "https://x.com/h"


def test_webhook_action_without_url_raises(session):
    action = WorkflowAction(action_type="WEBHOOK", config={})

    with pytest.raises(ValueError):
        run_action(action, _context(session))


def test_slack_action_posts(session, monkeypatch):
    monkeypatch.setattr(
        "app.engine.actions.SlackClient.send_message",
        lambda webhook_url, message: FakeResponse(),
    )

    action = WorkflowAction(
        action_type="SLACK", config={"webhook_url": "https://hooks/x"}
    )

    assert run_action(action, _context(session))["status"] == 200


def test_unknown_action_type_raises(session):
    action = WorkflowAction(action_type="TELEPATHY", config={})

    with pytest.raises(ValueError):
        run_action(action, _context(session))


async def test_notification_action_writes_rows(client, accounts, session):
    action = WorkflowAction(
        action_type="NOTIFICATION",
        config={"title": "Failed", "message": "Amount {amount}"},
    )

    context = ActionContext(
        session=session,
        organization_id=accounts["org_id"],
        workflow_id=1,
        execution_id=1,
        payload={"amount": 500},
    )

    result = run_action(action, context)

    assert result["recipients"] == 2

    rows = session.query(Notification).all()
    assert len(rows) == 2
    assert rows[0].message == "Amount 500"

    listed = await client.get(
        "/api/v1/notifications", headers=accounts["owner"]["headers"]
    )
    assert len(listed.json()) == 1


# ---------------------------------------------------------------- execution flow


async def test_execution_runs_actions_and_succeeds(
    client, accounts, workflow, session, realtime
):
    await client.post(
        f"/api/v1/workflows/{workflow['id']}/actions",
        json={
            "action_type": "NOTIFICATION",
            "config": {"title": "Payment", "message": "Amount {amount}"},
            "execution_order": 1,
        },
        headers=accounts["owner"]["headers"],
    )

    ids = handle_event(session, envelope(accounts["org_id"]))

    execution = ExecutionService.get(session, ids[0])
    session.refresh(execution)

    assert execution.status == WorkflowStatus.SUCCESS.value
    assert execution.completed_at is not None
    assert session.query(Notification).count() == 2

    statuses = [m["status"] for m in realtime]
    assert WorkflowStatus.RUNNING.value in statuses
    assert WorkflowStatus.SUCCESS.value in statuses


async def test_execution_without_actions_succeeds(
    client, accounts, workflow, session
):
    ids = handle_event(session, envelope(accounts["org_id"]))

    execution = ExecutionService.get(session, ids[0])
    session.refresh(execution)

    assert execution.status == WorkflowStatus.SUCCESS.value


async def test_failed_action_marks_execution_failed_and_dead_letters(
    client, accounts, workflow, session, monkeypatch
):
    dead_lettered = []

    monkeypatch.setattr(
        "app.workers.tasks.workflow_tasks.RabbitMQPublisher.publish_dead_letter",
        dead_lettered.append,
    )

    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    workflow_tasks._finalize_failure(ids[0], RuntimeError("smtp exploded"))

    execution = ExecutionService.get(session, ids[0])
    session.refresh(execution)

    assert execution.status == WorkflowStatus.FAILED.value
    assert "smtp exploded" in execution.error_message
    assert len(dead_lettered) == 1
    assert dead_lettered[0]["execution_id"] == ids[0]
    assert dead_lettered[0]["organization_id"] == accounts["org_id"]


async def test_action_task_failure_hook_finalizes(
    client, accounts, workflow, session, monkeypatch
):
    captured = []

    monkeypatch.setattr(
        "app.workers.tasks.workflow_tasks._finalize_failure",
        lambda execution_id, exc: captured.append((execution_id, str(exc))),
    )

    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    workflow_tasks.ActionTask().on_failure(
        RuntimeError("boom"), "task-id", (ids[0], 1), {}, None
    )

    assert captured == [(ids[0], "boom")]


async def test_missing_execution_is_handled(client, accounts, workflow):
    assert workflow_tasks.execute_workflow.run(999999)["status"] == "MISSING"
    assert workflow_tasks.complete_execution.run(999999)["status"] == "MISSING"
    assert workflow_tasks.retry_execution.run(999999)["status"] == "MISSING"


async def test_retry_execution_requeues(client, accounts, workflow, session):
    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    result = workflow_tasks.retry_execution.run(ids[0])

    assert result["status"] == "REQUEUED"

    execution = ExecutionService.get(session, ids[0])
    session.refresh(execution)
    assert execution.retry_count >= 1


# ---------------------------------------------------------------- cleanup


async def test_cleanup_removes_only_old_terminal_executions(
    client, accounts, workflow, session
):
    old_success = WorkflowExecution(
        workflow_id=workflow["id"],
        event_id="old-success",
        status=WorkflowStatus.SUCCESS.value,
        event_payload={},
        started_at=datetime.utcnow() - timedelta(days=90),
    )
    old_running = WorkflowExecution(
        workflow_id=workflow["id"],
        event_id="old-running",
        status=WorkflowStatus.RUNNING.value,
        event_payload={},
        started_at=datetime.utcnow() - timedelta(days=90),
    )
    recent_success = WorkflowExecution(
        workflow_id=workflow["id"],
        event_id="recent",
        status=WorkflowStatus.SUCCESS.value,
        event_payload={},
        started_at=datetime.utcnow(),
    )

    session.add_all([old_success, old_running, recent_success])
    session.commit()

    result = cleanup_old_logs.run(retention_days=30)

    assert result["deleted"] == 1

    remaining = {e.event_id for e in session.query(WorkflowExecution).all()}
    assert remaining == {"old-running", "recent"}
