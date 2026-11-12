async def test_member_cannot_write_but_can_read(client, accounts, workflow):
    member = accounts["member"]["headers"]
    org_id = accounts["org_id"]

    resp = await client.get(
        f"/api/v1/workflows?organization_id={org_id}", headers=member
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "name": "Nope",
            "trigger_type": "user.created",
        },
        headers=member,
    )
    assert resp.status_code == 403


async def test_outsider_is_blocked_from_every_workflow_route(
    client, accounts, workflow
):
    outsider = accounts["outsider"]["headers"]
    org_id = accounts["org_id"]
    wf_id = workflow["id"]

    assert (
        await client.get(f"/api/v1/workflows?organization_id={org_id}", headers=outsider)
    ).status_code == 403
    assert (
        await client.get(f"/api/v1/workflows/{wf_id}", headers=outsider)
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/workflows/{wf_id}", headers=outsider)
    ).status_code == 403


async def test_actions_crud_and_ordering(client, accounts, workflow):
    owner = accounts["owner"]["headers"]
    member = accounts["member"]["headers"]
    wf_id = workflow["id"]

    first = await client.post(
        f"/api/v1/workflows/{wf_id}/actions",
        json={"action_type": "EMAIL", "config": {"to": "a@x.com"}, "execution_order": 2},
        headers=owner,
    )
    assert first.status_code == 201

    await client.post(
        f"/api/v1/workflows/{wf_id}/actions",
        json={
            "action_type": "WEBHOOK",
            "config": {"url": "https://x.com/h"},
            "execution_order": 1,
        },
        headers=owner,
    )

    listed = await client.get(f"/api/v1/workflows/{wf_id}/actions", headers=member)
    assert [a["execution_order"] for a in listed.json()] == [1, 2]

    bad = await client.post(
        f"/api/v1/workflows/{wf_id}/actions",
        json={"action_type": "TELEPATHY", "config": {}},
        headers=owner,
    )
    assert bad.status_code == 422

    denied = await client.post(
        f"/api/v1/workflows/{wf_id}/actions",
        json={"action_type": "EMAIL", "config": {}},
        headers=member,
    )
    assert denied.status_code == 403

    action_id = first.json()["id"]
    updated = await client.patch(
        f"/api/v1/workflows/{wf_id}/actions/{action_id}",
        json={"config": {"to": "b@x.com"}},
        headers=owner,
    )
    assert updated.json()["config"] == {"to": "b@x.com"}
    assert updated.json()["action_type"] == "EMAIL"

    assert (
        await client.delete(
            f"/api/v1/workflows/{wf_id}/actions/{action_id}", headers=owner
        )
    ).status_code == 200


async def test_conditions_crud(client, accounts, workflow):
    owner = accounts["owner"]["headers"]
    wf_id = workflow["id"]

    created = await client.post(
        f"/api/v1/workflows/{wf_id}/conditions",
        json={"field": "amount", "operator": "gt", "value": 100},
        headers=owner,
    )
    assert created.status_code == 201

    bad = await client.post(
        f"/api/v1/workflows/{wf_id}/conditions",
        json={"field": "amount", "operator": "approximately", "value": 1},
        headers=owner,
    )
    assert bad.status_code == 422

    updated = await client.patch(
        f"/api/v1/workflows/{wf_id}/conditions/{created.json()['id']}",
        json={"operator": "gte", "value": 250},
        headers=owner,
    )
    assert updated.json()["operator"] == "gte"
    assert updated.json()["value"] == 250


async def test_action_from_another_workflow_is_not_found(client, accounts, workflow):
    owner = accounts["owner"]["headers"]

    other = await client.post(
        "/api/v1/workflows",
        json={
            "organization_id": accounts["org_id"],
            "name": "Other",
            "trigger_type": "user.created",
        },
        headers=owner,
    )
    other_id = other.json()["id"]

    action = await client.post(
        f"/api/v1/workflows/{workflow['id']}/actions",
        json={"action_type": "EMAIL", "config": {"to": "a@x.com"}},
        headers=owner,
    )

    resp = await client.get(
        f"/api/v1/workflows/{other_id}/actions/{action.json()['id']}", headers=owner
    )

    assert resp.status_code == 404
