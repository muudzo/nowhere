from fastapi import Request, Response, HTTPException, Depends
from redis.asyncio import Redis
from ..infra.persistence.redis import get_redis_client
from ..infra.persistence.keys import RedisKeys
from .deps import get_current_user_id
import logging

logger = logging.getLogger(__name__)

from .schemas import CreateIntentRequest
from ..infra.persistence.intent_repo import IntentRepository

class RateLimiter:
    def __init__(self, action: str, limit: int, window: int = 3600):
        self.action = action
        self.limit = limit
        self.window = window

    async def check_limit(self, user_id: str, redis: Redis, limit_override: int = None):
        key = RedisKeys.rate_limit(user_id, self.action)
        effective_limit = limit_override if limit_override is not None else self.limit
        
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.window)
            
        if current > effective_limit:
            wait_time = await redis.ttl(key)
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded for {self.action} (Limit: {effective_limit}). Try again in {wait_time} seconds."
            )

    async def __call__(
        self, 
        request: Request, 
        user_id: str = Depends(get_current_user_id),
        redis: Redis = Depends(get_redis_client)
    ):
        await self.check_limit(user_id, redis)
        return True

class DynamicRateLimiter(RateLimiter):
    """
    Adjusts rate limit based on density of intents in the area.
    """
    async def __call__(
        self,
        request: Request,
        intent_request: CreateIntentRequest,
        user_id: str = Depends(get_current_user_id),
        redis: Redis = Depends(get_redis_client),
        repo: IntentRepository = Depends()
    ):
        # Calculate dynamic limit
        limit = self.limit
        count = 0
        
        try:
            count = await repo.count_nearby(intent_request.latitude, intent_request.longitude, radius_km=1.0)
            if count > 50:
                limit = max(1, int(self.limit * 0.2)) # Harsh reduction in super dense areas
            elif count > 20:
                limit = max(1, int(self.limit * 0.5))
        except Exception as e:
            logger.error(f"Failed to check density: {e}")
            # Fallback to default limit
             
        await self.check_limit(user_id, redis, limit_override=limit)
        return True

async def rate_limit(request: Request):
    pass
