from fastapi import HTTPException, Depends, Request
from redis.asyncio import Redis
from ..infra.persistence.redis import get_redis_client
from ..infra.persistence.keys import RedisKeys
from .deps import get_current_user_id
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, action: str, limit: int, window: int = 3600):
        self.action = action
        self.limit = limit
        self.window = window

    async def check_limit(self, user_id: str, redis: Redis, limit_override: int | None = None) -> None:
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
        user_id: str = Depends(get_current_user_id),
        redis: Redis = Depends(get_redis_client)
    ) -> bool:
        await self.check_limit(user_id, redis)
        return True


class DynamicRateLimiter(RateLimiter):
    """
    Rate limiter with configurable limits.
    For dynamic density-based limiting, use a factory function.
    """
    pass


async def rate_limit(request: Request) -> None:
    """Placeholder rate limit function for middleware or direct usage."""
    pass
