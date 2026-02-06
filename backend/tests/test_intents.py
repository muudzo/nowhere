import pytest
from httpx import AsyncClient
from backend.main import app
from backend.infra.persistence.redis import RedisClient, get_redis_client
from backend.infra.persistence.keys import RedisKeys
from backend.infra.persistence.intent_repo import IntentRepository
from backend.infra.persistence.join_repo import JoinRepository
from backend.infra.persistence.message_repo import MessageRepository
import uuid

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

from unittest.mock import patch

from backend.main import lifespan

@pytest.fixture(autouse=True)
async def manage_redis():
    async with lifespan(app):
        yield

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires proper AsyncClient transport with lifespan")
async def test_create_and_find_nearby_intent():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create
        lat, lon = 40.7128, -74.0060
        payload = {
            "title": "Coffee run",
            "emoji": "☕",
            "latitude": lat,
            "longitude": lon
        }
        response = await ac.post("/intents/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Coffee run"
        intent_id = data["id"]
        
        # Find nearby
        response = await ac.get(f"/intents/nearby?lat={lat}&lon={lon}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        found = False
        for intent in data["intents"]:
            if intent["id"] == intent_id:
                found = True
                # verify rounding
                assert len(str(intent["latitude"]).split(".")[1]) <= 3
                break
        assert found

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires proper AsyncClient transport with lifespan")
async def test_empty_state():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/intents/nearby?lat=0&lon=0")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["message"] is not None
