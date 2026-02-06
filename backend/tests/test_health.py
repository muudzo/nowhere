import pytest


@pytest.mark.asyncio
async def test_health_endpoint_exists(app):
    """Verify /health endpoint is registered on the app."""
    # Check that the app has the /health route
    routes = [route.path for route in app.routes]
    assert "/health" in routes
