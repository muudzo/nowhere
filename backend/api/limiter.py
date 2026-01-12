from fastapi import Request, HTTPException, Depends
from redis.asyncio import Redis
from ..storage.redis import get_redis_client
from ..storage.keys import RedisKeys
from .deps import get_current_user_id
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, action: str, limit: int, window: int = 3600):
        self.action = action
        self.limit = limit
        self.window = window

    async def __call__(
        self, 
        request: Request, 
        user_id: str = Depends(get_current_user_id),
        redis: Redis = Depends(get_redis_client)
    ):
        key = RedisKeys.rate_limit(user_id, self.action)
        
        # Fixed window simpler approach:
        # INCR key. If 1, set expire.
        # If > limit, 429.
        
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.window)
            
        if current > self.limit:
            wait_time = await redis.ttl(key)
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded for {self.action}. Try again in {wait_time} seconds."
            )
            
        return True

# Default dummy (deprecated, for backward compat if needed temporarily)
async def rate_limit(request: Request):
    pass
