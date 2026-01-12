from fastapi import Request, HTTPException
from uuid import UUID

def get_current_user_id(request: Request) -> UUID:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # Should be caught by middleware normally, but defensive check
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID")

from fastapi import Depends
from redis.asyncio import Redis
from ..storage.redis import get_redis_client
from ..spam import SpamDetector

def get_spam_detector(redis: Redis = Depends(get_redis_client)) -> SpamDetector:
    return SpamDetector(redis)
