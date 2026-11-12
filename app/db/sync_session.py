from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db import models as _models  # noqa: F401 — register ORM mappers

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


@contextmanager
def session_scope():
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
