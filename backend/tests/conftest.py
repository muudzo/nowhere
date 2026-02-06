import asyncio
import os
import pytest

import httpx
import fakeredis
import asyncpg

from testcontainers.postgres import PostgresContainer


# Provide an event loop for pytest-asyncio with session scope
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# FastAPI app fixture - imports the app object from the project
# Import here to avoid expensive side-effects at collection time
@pytest.fixture(scope="session")
def app():
    from backend.api.main import app as _app

    return _app


# Postgres container fixture using Testcontainers
# Starts a transient Postgres instance and patches the project's
# `create_postgres_pool` to use a connection pool to this container.
@pytest.fixture(scope="session")
def postgres_container(monkeypatch):
    container = PostgresContainer("postgres:15")
    container.start()

    # Testcontainers exposes a SQLAlchemy-style URL; asyncpg accepts it too
    dsn = container.get_connection_url()

    async def _create_pool(dsn_in: str):
        # Create an asyncpg pool connected to the provided DSN
        pool = await asyncpg.create_pool(dsn_in)
        return pool

    # Patch the project's create_postgres_pool to ensure the app uses our container
    monkeypatch.setattr(
        "backend.infrastructure.postgres.repo.create_postgres_pool",
        _create_pool,
        raising=False,
    )

    yield dsn

    try:
        container.stop()
    except Exception:
        pass


# Fake Redis fixture using fakeredis
# Patches `create_redis` in the project to return a FakeRedis instance
@pytest.fixture
async def redis_fixture(monkeypatch):
    server = fakeredis.FakeServer()
    fake_redis = fakeredis.FakeRedis(server=server, decode_responses=True)

    async def _create_redis(dsn: str):
        # Return the same fake redis instance for tests
        return fake_redis

    monkeypatch.setattr(
        "backend.infrastructure.redis.repo.create_redis",
        _create_redis,
        raising=False,
    )

    yield fake_redis

    # cleanup
    try:
        await fake_redis.flushall()
    except Exception:
        pass


# Async HTTP client for testing FastAPI endpoints.
# Relies on patched startup functions (postgres_container and redis_fixture)
@pytest.fixture
async def async_client(app, postgres_container, redis_fixture):
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
