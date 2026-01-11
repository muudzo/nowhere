from fastapi import HTTPException
from starlette.requests import Request
from ..storage.redis import RedisClient

async def rate_limit(request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    key = f"rate_limit:{user_id}"
    
    redis = RedisClient.get_client()
    
    # Simple fixed window: 10 requests per minute
    # INCR key
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
        
    if current > 60:
        raise HTTPException(status_code=429, detail="Too many requests")
