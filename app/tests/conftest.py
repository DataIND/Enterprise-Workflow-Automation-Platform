import os
import tempfile

# Must be set before anything imports app.core.config, which builds the
# engines at import time.
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "ewap_pytest.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.db.sync_session import SyncSessionLocal  # noqa: E402
from app.events.async_publisher import AsyncEventPublisher  # noqa: E402
from app.main import app  # noqa: E402
from app.websocket import redis_bridge  # noqa: E402
from app.workers.celery_app import celery_app  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = False


@pytest_asyncio.fixture
async def db_setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_setup):
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def session():
    db = SyncSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def published(monkeypatch):
    """Capture envelopes instead of hitting RabbitMQ."""

    messages = []

    async def fake_publish(cls, message, routing_key=None):
        messages.append(message)

    monkeypatch.setattr(
        AsyncEventPublisher, "publish", classmethod(fake_publish), raising=True
    )

    return messages


@pytest.fixture(autouse=True)
def realtime(monkeypatch):
    """Capture realtime events instead of hitting Redis."""

    messages = []

    monkeypatch.setattr(redis_bridge, "publish_event", messages.append)

    return messages


@pytest_asyncio.fixture
async def accounts(client):
    """Owner + member in one org, plus an unrelated outsider."""

    async def register(email):
        await client.post(
            "/api/v1/auth/register", json={"email": email, "password": "pw123456"}
        )
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "pw123456"}
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me = await client.get("/api/v1/auth/me", headers=headers)
        return {"headers": headers, "id": me.json()["id"]}

    owner = await register("owner@test.com")
    member = await register("member@test.com")
    outsider = await register("outsider@test.com")

    org = await client.post(
        "/api/v1/organizations", json={"name": "Acme"}, headers=owner["headers"]
    )
    org_id = org.json()["id"]

    await client.post(
        f"/api/v1/organizations/{org_id}/invite",
        json={"user_id": member["id"], "role": "MEMBER"},
        headers=owner["headers"],
    )

    return {
        "owner": owner,
        "member": member,
        "outsider": outsider,
        "org_id": org_id,
    }


@pytest_asyncio.fixture
async def workflow(client, accounts):
    resp = await client.post(
        "/api/v1/workflows",
        json={
            "organization_id": accounts["org_id"],
            "name": "On payment failed",
            "trigger_type": "payment.failed",
        },
        headers=accounts["owner"]["headers"],
    )

    return resp.json()


def sync_session():
    return SyncSessionLocal()
