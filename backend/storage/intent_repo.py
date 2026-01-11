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
