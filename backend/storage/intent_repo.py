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
        return Intent.model_validate_json(data)

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0) -> list[Intent]:
        # radius in km
        # GEOSEARCH key FROMLLONLAT lon lat BYRADIUS radius km ASC
        # Returns list of members
        member_ids = await self.redis.geosearch(
            "intents:geo",
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km"
        )
        
        if not member_ids:
            return []

        # Fetch all intents
        # member_ids in redis-py might be bytes or strings depending on decode_responses.
        # We configured decode_responses=True in RedisClient.
        
        # MGET to get all intent:id
        keys = [f"intent:{mid}" for mid in member_ids]
        json_list = await self.redis.mget(keys)
        
        # Filter out None (expired) and parse
        intents = []
        expired_members = []
        
        for i, json_str in enumerate(json_list):
            if json_str:
                intents.append(Intent.model_validate_json(json_str))
            else:
                # Track expired member for cleanup
                expired_members.append(member_ids[i])
        
        if expired_members:
            # Clean up zombies from the geo index
            await self.redis.zrem("intents:geo", *expired_members)
            logger.info(f"Cleaned up {len(expired_members)} expired intents from geo index")
        
        return intents
