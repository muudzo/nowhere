from datetime import datetime, timedelta, timezone
import logging
from ..domain.intent import Intent
from backend.storage.redis import RedisClient, get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

INTENT_TTL_SECONDS = 86400  # 24 hours

class IntentRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client)):
        self.redis = redis

    async def save_intent(self, intent: Intent) -> None:
        key = RedisKeys.intent(intent.id)
        # Convert pydantic model to json
        data = intent.model_dump_json()
        await self.redis.set(key, data, ex=INTENT_TTL_SECONDS)
        
        # Add to geo index
        # GEOADD key longitude latitude member
        await self.redis.geoadd(RedisKeys.intent_geo(), (intent.longitude, intent.latitude, str(intent.id)))
        
        logger.info(f"Saved intent {intent.id} with TTL {INTENT_TTL_SECONDS}s")

    async def get_intent(self, intent_id: str) -> Intent | None:
        key = RedisKeys.intent(intent_id)
        data = await self.redis.get(key)
        if not data:
            return None
        intent = Intent.model_validate_json(data)
        
        # Populate join count
        join_key = RedisKeys.intent_joins(intent_id)
        count = await self.redis.scard(join_key)
        # We need to manually update the field since the model is frozen and it was loaded from JSON without it (or with default 0).
        # Actually Pydantic models with frozen=True invoke copy to update.
        # But wait, create_intent saves with default 0.
        # So we just need to overwrite it with the fresh count from Redis.
        # Using model_copy with update.
        intent = intent.model_copy(update={"join_count": count})
        return intent

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50) -> list[Intent]:
        # Fetch 2x limit to allow for ranking and filtering
        fetch_count = limit * 2
        
        # GEOSEARCH with distance
        results = await self.redis.geosearch(
            RedisKeys.intent_geo(),
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            count=fetch_count,
            withdist=True
        )
        
        if not results:
            return []

        # results is list of (member, distance) tuples
        member_ids = [m[0] for m in results]
        distances = {m[0]: m[1] for m in results} # Map id -> dist

        keys = [RedisKeys.intent(mid) for mid in member_ids]
        json_list = await self.redis.mget(keys)
        
        candidates = []
        expired_members = []
        
        # Pipeline for join counts
        pipeline = self.redis.pipeline()
        valid_indices = []

        for i, json_str in enumerate(json_list):
            if json_str:
                intent = Intent.model_validate_json(json_str)
                if intent.flags < 3:
                    candidates.append(intent)
                    pipeline.scard(RedisKeys.intent_joins(intent.id))
            else:
                expired_members.append(member_ids[i])
        
        if not candidates:
            if expired_members:
                await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
            return []

        # Execute pipeline to get counts
        counts = await pipeline.execute()
        
        # Scoring logic
        # Weights
        W_DIST = 1.0
        W_FRESH = 2.0
        W_POP = 0.5
        
        scored_intents = []
        now = datetime.now(timezone.utc)
        
        for intent, count in zip(candidates, counts):
            # Update count
            intent = intent.model_copy(update={"join_count": count})
            
            # 1. Distance Score (0 to 1, 1 is closest)
            dist = distances.get(str(intent.id), radius_km)
            
            # Commit 7: Visibility Thresholds
            # If join_count == 0 (unverified) and not system, max radius is 0.2km (200m).
            if intent.join_count == 0 and not intent.is_system and dist > 0.2:
                continue

            # Normalize: 1 - (dist / radius)
            # If dist > radius (unlikely with geosearch), clamp to 0
            dist_score = max(0, 1.0 - (dist / radius_km))
            
            # 2. Freshness Score (Decay over 24h)
            # 0h old -> 1.0
            # 24h old -> 0.0
            created_at = intent.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            age_seconds = (now - created_at).total_seconds()
            freshness_score = max(0, 1.0 - (age_seconds / 86400.0))
            
            # 3. Popularity Score (Logarithmic)
            # 0 joins -> 0
            # 10 joins -> log(11) ~ 2.4
            # Cap impact?
            from math import log1p
            pop_score = log1p(count) 
            
            total_score = (W_DIST * dist_score) + (W_FRESH * freshness_score) + (W_POP * pop_score)
            
            scored_intents.append((total_score, intent))
            
        # Cleanup expired
        if expired_members:
             await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
             
        # Sort by score descending
        scored_intents.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 'limit' intents
        return [item[1] for item in scored_intents[:limit]]

    async def flag_intent(self, intent_id: UUID) -> int:
        key = RedisKeys.intent(intent_id)
        data = await self.redis.get(key)
        if not data:
            return 0
            
        intent = Intent.model_validate_json(data)
        intent = intent.model_copy(update={"flags": intent.flags + 1})
        
        # Save back. We should use a lua script for atomicity but MVP.
        # Preserve TTL?
        ttl = await self.redis.ttl(key)
        if ttl > 0:
            await self.redis.set(key, intent.model_dump_json(), ex=ttl)
            
        return intent.flags

