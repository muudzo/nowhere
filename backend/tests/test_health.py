import pytest


@pytest.mark.asyncio
async def test_health(async_client):
    """Smoke test for the /health endpoint.

    The endpoint performs lightweight readiness checks (Redis ping
    and a simple Postgres query). With fixtures patched, this should
    return HTTP 200 and a JSON body {"status": "ok"}.
    """
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
