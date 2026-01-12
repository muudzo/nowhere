import logging
from uuid import UUID
from backend.storage.redis import RedisClient, get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class JoinRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client)):
        self.redis = redis

    async def save_join(self, intent_id: UUID, user_id: UUID) -> bool:
        """
        Adds user to intent joins.
        Returns True if added, False if already joined.
        Raises ValueError if intent does not exist.
        """
        intent_key = RedisKeys.intent(intent_id)
        join_key = RedisKeys.intent_joins(intent_id)
        
        # Check if intent exists and get its TTL
        ttl = await self.redis.ttl(intent_key)
        
        if ttl <= 0:
            # -2 means key does not exist, -1 means no expiry (shouldn't happen for intents)
            # If 0, it's about to expire.
            # In any invalid case, we can't join.
            # We might want to throw an error or just return False.
            # Prompt says: "TTL matching intent". If intent is gone, can't join.
            raise ValueError("Intent not found or expired")

        # Add to set
        # SADD key member
        added = await self.redis.sadd(join_key, str(user_id))
        
        if added:
            # Set TTL on the set to match the intent (approx)
            # We rely on the initial TTL read. It might handle race conditions poorly but MVP.
            await self.redis.expire(join_key, ttl)
            logger.info(f"User {user_id} joined intent {intent_id}. TTL set to {ttl}s")
            return True
        
        return False

    async def get_join_count(self, intent_id: UUID) -> int:
        join_key = RedisKeys.intent_joins(intent_id)
        return await self.redis.scard(join_key)

    async def is_member(self, intent_id: UUID, user_id: UUID) -> bool:
        join_key = RedisKeys.intent_joins(intent_id)
        return await self.redis.sismember(join_key, str(user_id))
