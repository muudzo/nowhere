import asyncio
import os
import pytest

import httpx
import fakeredis

from testcontainers.postgres import PostgresContainer


# FastAPI app fixture - imports the app object from the project
@pytest.fixture(scope="session")
def app():
    from backend.api.main import app as _app
    return _app


# Postgres container fixture using Testcontainers
@pytest.fixture(scope="session")
def postgres_container():
    try:
        container = PostgresContainer("postgres:15")
        container.start()
        dsn = container.get_connection_url()
        # Convert psycopg2 format to asyncpg format
        dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
        
        yield dsn

        try:
            container.stop()
        except Exception:
            pass
    except Exception:
        # If testcontainers fails, just yield a dummy DSN
        yield "postgresql://test:test@localhost:5432/test"


# Fake Redis fixture using fakeredis
@pytest.fixture(scope="session")
def redis_fixture():
    server = fakeredis.FakeServer()
    fake_redis = fakeredis.FakeRedis(server=server, decode_responses=True)

    yield fake_redis

    try:
        fake_redis.flushall()
    except Exception:
        pass


# Async HTTP client for testing FastAPI endpoints
@pytest.fixture
async def async_client(app):
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
