import json

import pytest

from app.engine.event_handler import handle_event, parse_envelope
from app.events import consumer as event_consumer
from app.services.execution_service import ExecutionService
from app.utils.enums import WorkflowStatus


class FakeChannel:
    def __init__(self):
        self.acked = []
        self.nacked = []

    def basic_ack(self, delivery_tag):
        self.acked.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue):
        self.nacked.append((delivery_tag, requeue))


class FakeMethod:
    def __init__(self, delivery_tag=1, redelivered=False):
        self.delivery_tag = delivery_tag
        self.redelivered = redelivered


def envelope(org_id, event_type="payment.failed", payload=None, event_id="evt-1"):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "organization_id": org_id,
        "payload": payload if payload is not None else {"amount": 500},
    }


# ---------------------------------------------------------------- publish API


async def test_publish_requires_authentication(client, accounts):
    resp = await client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "payment.failed",
            "organization_id": accounts["org_id"],
            "payload": {},
        },
    )

    assert resp.status_code == 401


async def test_publish_rejects_other_organizations(client, accounts, published):
    resp = await client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "payment.failed",
            "organization_id": accounts["org_id"],
            "payload": {"amount": 1},
        },
        headers=accounts["outsider"]["headers"],
    )

    assert resp.status_code == 403
    assert published == []


async def test_publish_returns_envelope_with_event_id(client, accounts, published):
    resp = await client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "payment.failed",
            "organization_id": accounts["org_id"],
            "payload": {"amount": 1},
        },
        headers=accounts["member"]["headers"],
    )

    assert resp.status_code == 202
    body = resp.json()
    assert body["event_id"]
    assert len(published) == 1
    assert published[0]["event_id"] == body["event_id"]
    assert published[0]["payload"] == {"amount": 1}


async def test_publish_preserves_client_event_id(client, accounts, published):
    resp = await client.post(
        "/api/v1/events/publish",
        json={
            "event_type": "payment.failed",
            "organization_id": accounts["org_id"],
            "payload": {},
            "event_id": "client-supplied",
        },
        headers=accounts["owner"]["headers"],
    )

    assert resp.json()["event_id"] == "client-supplied"


# ---------------------------------------------------------------- envelope parsing


def test_parse_envelope_accepts_bytes():
    raw = json.dumps(envelope(1)).encode()

    assert parse_envelope(raw)["event_type"] == "payment.failed"


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        json.dumps({"event_type": "x", "organization_id": 1}),  # no payload
        json.dumps({"organization_id": 1, "payload": {}}),  # no event_type
        json.dumps({"event_type": "x", "organization_id": 1, "payload": "nope"}),
        json.dumps([1, 2, 3]),
    ],
)
def test_parse_envelope_rejects_malformed(body):
    with pytest.raises(ValueError):
        parse_envelope(body)


# ---------------------------------------------------------------- engine matching


async def test_event_creates_execution(client, accounts, workflow, session, realtime):
    dispatched = []

    ids = handle_event(
        session, envelope(accounts["org_id"]), dispatch=dispatched.append
    )

    assert len(ids) == 1
    assert dispatched == ids

    execution = ExecutionService.get(session, ids[0])
    assert execution.workflow_id == workflow["id"]
    assert execution.status == WorkflowStatus.PENDING.value
    assert execution.event_id == "evt-1"

    assert realtime and realtime[-1]["status"] == WorkflowStatus.PENDING.value
    assert accounts["owner"]["id"] in realtime[-1]["user_ids"]


async def test_unmatched_trigger_type_creates_nothing(
    client, accounts, workflow, session
):
    ids = handle_event(
        session,
        envelope(accounts["org_id"], event_type="user.created"),
        dispatch=lambda _: None,
    )

    assert ids == []


async def test_other_organization_does_not_match(client, accounts, workflow, session):
    ids = handle_event(
        session, envelope(accounts["org_id"] + 999), dispatch=lambda _: None
    )

    assert ids == []


async def test_inactive_workflow_does_not_match(client, accounts, workflow, session):
    await client.patch(
        f"/api/v1/workflows/{workflow['id']}",
        json={"is_active": False},
        headers=accounts["owner"]["headers"],
    )

    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    assert ids == []


async def test_conditions_gate_execution(client, accounts, workflow, session):
    await client.post(
        f"/api/v1/workflows/{workflow['id']}/conditions",
        json={"field": "amount", "operator": "gt", "value": 100},
        headers=accounts["owner"]["headers"],
    )

    blocked = handle_event(
        session,
        envelope(accounts["org_id"], payload={"amount": 5}, event_id="low"),
        dispatch=lambda _: None,
    )
    assert blocked == []

    allowed = handle_event(
        session,
        envelope(accounts["org_id"], payload={"amount": 500}, event_id="high"),
        dispatch=lambda _: None,
    )
    assert len(allowed) == 1


async def test_duplicate_event_id_is_ignored(client, accounts, workflow, session):
    first = handle_event(
        session, envelope(accounts["org_id"]), dispatch=lambda _: None
    )
    second = handle_event(
        session, envelope(accounts["org_id"]), dispatch=lambda _: None
    )

    assert len(first) == 1
    assert second == []


async def test_distinct_event_ids_both_run(client, accounts, workflow, session):
    first = handle_event(
        session, envelope(accounts["org_id"], event_id="a"), dispatch=lambda _: None
    )
    second = handle_event(
        session, envelope(accounts["org_id"], event_id="b"), dispatch=lambda _: None
    )

    assert len(first) == 1 and len(second) == 1


# ---------------------------------------------------------------- consumer


async def test_consumer_acks_a_handled_message(
    client, accounts, workflow, session, monkeypatch
):
    monkeypatch.setattr(event_consumer, "handle_event", lambda s, e: [1])

    channel = FakeChannel()

    event_consumer.on_message(
        channel,
        FakeMethod(delivery_tag=7),
        None,
        json.dumps(envelope(accounts["org_id"])).encode(),
    )

    assert channel.acked == [7]
    assert channel.nacked == []


def test_consumer_dead_letters_malformed_messages():
    channel = FakeChannel()

    event_consumer.on_message(channel, FakeMethod(delivery_tag=3), None, b"{oops")

    # requeue=False routes the message to the dead letter exchange.
    assert channel.nacked == [(3, False)]
    assert channel.acked == []


async def test_consumer_requeues_once_on_transient_failure(
    client, accounts, monkeypatch
):
    def explode(session, envelope_):
        raise RuntimeError("database is down")

    monkeypatch.setattr(event_consumer, "handle_event", explode)

    body = json.dumps(envelope(accounts["org_id"])).encode()

    first = FakeChannel()
    event_consumer.on_message(first, FakeMethod(delivery_tag=1), None, body)
    assert first.nacked == [(1, True)]

    redelivered = FakeChannel()
    event_consumer.on_message(
        redelivered, FakeMethod(delivery_tag=1, redelivered=True), None, body
    )
    assert redelivered.nacked == [(1, False)]


async def test_consumer_creates_an_execution_end_to_end(
    client, accounts, workflow, session
):
    channel = FakeChannel()

    event_consumer.on_message(
        channel,
        FakeMethod(delivery_tag=9),
        None,
        json.dumps(envelope(accounts["org_id"], event_id="from-broker")).encode(),
    )

    assert channel.acked == [9]

    listed = await client.get(
        f"/api/v1/executions?organization_id={accounts['org_id']}",
        headers=accounts["owner"]["headers"],
    )

    assert [e["event_id"] for e in listed.json()] == ["from-broker"]


# ---------------------------------------------------------------- executions API


async def test_executions_are_scoped_to_the_organization(
    client, accounts, workflow, session
):
    handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    org_id = accounts["org_id"]

    listed = await client.get(
        f"/api/v1/executions?organization_id={org_id}",
        headers=accounts["member"]["headers"],
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    denied = await client.get(
        f"/api/v1/executions?organization_id={org_id}",
        headers=accounts["outsider"]["headers"],
    )
    assert denied.status_code == 403

    anonymous = await client.get(f"/api/v1/executions?organization_id={org_id}")
    assert anonymous.status_code == 401


async def test_get_execution_by_id_enforces_membership(
    client, accounts, workflow, session
):
    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)
    execution_id = ids[0]

    ok = await client.get(
        f"/api/v1/executions/{execution_id}", headers=accounts["member"]["headers"]
    )
    assert ok.status_code == 200
    assert ok.json()["event_id"] == "evt-1"

    denied = await client.get(
        f"/api/v1/executions/{execution_id}", headers=accounts["outsider"]["headers"]
    )
    assert denied.status_code == 403

    missing = await client.get(
        "/api/v1/executions/999999", headers=accounts["owner"]["headers"]
    )
    assert missing.status_code == 404


async def test_executions_can_be_filtered_by_status(
    client, accounts, workflow, session
):
    ids = handle_event(session, envelope(accounts["org_id"]), dispatch=lambda _: None)

    execution = ExecutionService.get(session, ids[0])
    ExecutionService.mark_success(session, execution)

    org_id = accounts["org_id"]
    headers = accounts["owner"]["headers"]

    success = await client.get(
        f"/api/v1/executions?organization_id={org_id}&status=SUCCESS", headers=headers
    )
    assert len(success.json()) == 1

    failed = await client.get(
        f"/api/v1/executions?organization_id={org_id}&status=FAILED", headers=headers
    )
    assert failed.json() == []
