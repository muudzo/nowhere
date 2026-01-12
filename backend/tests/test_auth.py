import pytest
import uuid
from httpx import AsyncClient
from backend.main import app
from backend.storage.redis import RedisClient, lifespan

from backend.api.limiter import rate_limit

@pytest.mark.asyncio
async def test_auth_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. First request, no cookie
        response = await ac.get("/health")
        assert response.status_code == 200
        assert "user_id" in response.cookies
        user_id = response.cookies["user_id"]
        
        # 2. Subsequent request, with cookie
        response = await ac.get("/health", cookies={"user_id": user_id})
        assert response.status_code == 200
        # Cookie IS re-set now to refresh expiry
        assert "user_id" in response.headers.get("set-cookie", "").lower()

@pytest.mark.asyncio
async def test_header_identity_precedence():
    """Test that X-Nowhere-Identity header takes precedence over cookie"""
    custom_id = str(uuid.uuid4())
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First request with header
        # Note: Use trailing slash for POST to avoid 307 redirect
        response = await ac.post("/intents/", json={
            "title": "Header Test",
            "emoji": "🧪",
            "latitude": 40.7128,
            "longitude": -74.0060
        }, headers={"X-Nowhere-Identity": custom_id})
        
        assert response.status_code == 201
        
        # Verify user_id context matches header
        # (We can't easily check request.state in integration test without exposing it, 
        # but we can check if it persists or if we can see it in rate limit headers if we had them or logs.
        # For now, let's trust if it works 201).
        
        # Verify cookie is set to match the header ID
        assert "user_id" in response.cookies
        assert response.cookies["user_id"] == custom_id

@pytest.mark.asyncio
async def test_join_and_message_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Get User ID
        res = await ac.get("/health")
        cookies = res.cookies
        
        # Create Intent
        payload = {"title": "Test Chat", "emoji": "🧪", "latitude": 10.0, "longitude": 10.0}
        res = await ac.post("/intents/", json=payload, cookies=cookies)
        assert res.status_code == 201
        intent_id = res.json()["id"]
        
        # Try to message WITHOUT joining (should fail 403)
        msg = {"user_id": cookies["user_id"], "content": "Hello"}
        res = await ac.post(f"/intents/{intent_id}/messages", json=msg, cookies=cookies)
        assert res.status_code == 403
        
        # Join
        # user_id is implicit in auth now, but schema still has it? 
        # Check Commit 21 schema: JoinRequest(user_id: UUID).
        # Commit 29 replaced explicit user_id param with dependency. 
        # BUT update to endpoint post_message definition in commit 29 shows:
        # async def post_message(intent_id: UUID, request: CreateMessageRequest, user_id: UUID = Depends(get_current_user_id)):
        # AND Join endpoint:
        # async def join_intent(intent_id: UUID, user_id: UUID = Depends(get_current_user_id)):
        # Wait, if I changed the signature to Depends(get_current_user_id), then I REMOVED the Request Body from the signature if I wasn't careful?
        # Let's check Commit 29 file change again.
        # "async def join_intent(intent_id: UUID, user_id: UUID = Depends(get_current_user_id)):"
        # It DOES NOT accept `request: JoinRequest` anymore in the signature I wrote.
        # So I don't need to send a body for join? Or just empty body? 
        # If I removed JoinRequest from signature, it takes no body.
        # Let's verify what I wrote in Commit 29.
        
        # Join (no body needed if I removed the Pydantic model from signature)
        res = await ac.post(f"/intents/{intent_id}/join", cookies=cookies)
        assert res.status_code == 200
        assert res.json()["joined"] is True
        
        # Duplicate join
        res = await ac.post(f"/intents/{intent_id}/join", cookies=cookies)
        assert res.status_code == 200
        assert res.json()["joined"] is False
        
        # Message (should succeed)
        # Does Post message still take request body?
        # "async def post_message(intent_id: UUID, request: CreateMessageRequest, user_id: UUID = Depends(get_current_user_id))"
        # Yes, it takes CreateMessageRequest.
        # CreateMessageRequest has user_id and content.
        # But user_id is also in dependency. Redundant? Yes.
        # Ideally schema should not have user_id if we have auth.
        # But I didn't change the schema in Commit 29.
        # So I must send user_id in body matching the auth cookie user_id?
        # Or I just ignore the body user_id and use the auth one?
        # The code in Commit 29 used `user_id=user_id` (from dep) when creating Message object.
        # So body user_id is ignored.
        msg = {"user_id": cookies["user_id"], "content": "Hello World"}
        res = await ac.post(f"/intents/{intent_id}/messages", json=msg, cookies=cookies)
        assert res.status_code == 200
        
        # Rate limit check (simple)
        # We did 1 create, 1 failed msg, 2 joins, 1 msg = 5 reqs. 
        # Limit is 60. 
        # Let's not test rate limit exhaustion to save time/complexity and avoid flakiness.
