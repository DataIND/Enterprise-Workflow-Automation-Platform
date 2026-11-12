async def test_register_login_refresh_me(client):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": "a@test.com", "password": "pw123456"}
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/api/v1/auth/register", json={"email": "a@test.com", "password": "pw123456"}
    )
    assert resp.status_code == 409

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "a@test.com", "password": "pw123456"}
    )
    assert resp.status_code == 200
    tokens = resp.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "a@test.com"

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]


async def test_login_rejects_bad_password(client):
    await client.post(
        "/api/v1/auth/register", json={"email": "b@test.com", "password": "pw123456"}
    )

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "b@test.com", "password": "wrong"}
    )

    assert resp.status_code == 401


async def test_protected_route_requires_token(client):
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    bad = {"Authorization": "Bearer nonsense"}
    assert (await client.get("/api/v1/auth/me", headers=bad)).status_code == 401


async def test_refresh_token_is_not_an_access_token(client):
    await client.post(
        "/api/v1/auth/register", json={"email": "c@test.com", "password": "pw123456"}
    )
    tokens = (
        await client.post(
            "/api/v1/auth/login", json={"email": "c@test.com", "password": "pw123456"}
        )
    ).json()

    headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}

    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
