from datetime import timedelta
import logging
from ..domain.intent import Intent
from .redis import RedisClient

logger = logging.getLogger(__name__)

INTENT_TTL_SECONDS = 86400  # 24 hours

class IntentRepository:
    def __init__(self):
        self.redis = RedisClient.get_client()

    async def save_intent(self, intent: Intent) -> None:
        key = f"intent:{intent.id}"
        # Convert pydantic model to json
        data = intent.model_dump_json()
        await self.redis.set(key, data, ex=INTENT_TTL_SECONDS)
        
        # Add to geo index
        # GEOADD key longitude latitude member
        await self.redis.geoadd("intents:geo", (intent.longitude, intent.latitude, str(intent.id)))
        
        logger.info(f"Saved intent {intent.id} with TTL {INTENT_TTL_SECONDS}s")

    async def get_intent(self, intent_id: str) -> Intent | None:
        key = f"intent:{intent_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        intent = Intent.model_validate_json(data)
        
        # Populate join count
        join_key = f"intent:{intent_id}:joins"
        count = await self.redis.scard(join_key)
        # We need to manually update the field since the model is frozen and it was loaded from JSON without it (or with default 0).
        # Actually Pydantic models with frozen=True invoke copy to update.
        # But wait, create_intent saves with default 0.
        # So we just need to overwrite it with the fresh count from Redis.
        # Using model_copy with update.
        intent = intent.model_copy(update={"join_count": count})
        return intent

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50) -> list[Intent]:
        # radius in km
        # GEOSEARCH key FROMLLONLAT lon lat BYRADIUS radius km ASC
        # Returns list of members
        member_ids = await self.redis.geosearch(
            "intents:geo",
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            count=limit
        )
        
        if not member_ids:
            return []

        # Fetch all intents
        # member_ids in redis-py might be bytes or strings depending on decode_responses.
        # We configured decode_responses=True in RedisClient.
        
        # MGET to get all intent:id
        keys = [f"intent:{mid}" for mid in member_ids]
        json_list = await self.redis.mget(keys)
        
        # Filter out None and gather valid intents
        valid_intents = []
        expired_members = []
        valid_indices = []

        for i, json_str in enumerate(json_list):
            if json_str:
                intent = Intent.model_validate_json(json_str)
                # Filter flagged (threshold 3?)
                if intent.flags < 3:
                    valid_intents.append(intent)
                    valid_indices.append(i)
            else:
                expired_members.append(member_ids[i])

        if valid_intents:
            # Pipeline request for all join counts
            pipeline = self.redis.pipeline()
            for intent in valid_intents:
                pipeline.scard(f"intent:{intent.id}:joins")
            counts = await pipeline.execute()
            
            # Update intents with counts
            valid_intents = [
                intent.model_copy(update={"join_count": c}) 
                for intent, c in zip(valid_intents, counts)
            ]

        if expired_members:
            # Clean up zombies from the geo index
            await self.redis.zrem("intents:geo", *expired_members)
            logger.info(f"Cleaned up {len(expired_members)} expired intents from geo index")
        
        return valid_intents

    async def flag_intent(self, intent_id: UUID) -> int:
        key = f"intent:{intent_id}"
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
