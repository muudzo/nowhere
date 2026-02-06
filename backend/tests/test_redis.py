import pytest


@pytest.mark.asyncio
async def test_redis_ping(redis_fixture):
    """Verify that the fake Redis instance responds to PING.

    The `redis_fixture` yields a `fakeredis.FakeRedis` instance patched
    into the project's startup path, so `await redis.ping()` should
    return a truthy PONG-like response.
    """
    pong = await redis_fixture.ping()
    # Accept either True or the string 'PONG' depending on fakeredis/redis-py version
    assert pong in (True, "PONG", b"PONG")
