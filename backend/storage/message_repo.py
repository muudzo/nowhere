import logging
from uuid import UUID
from .redis import RedisClient
from ..domain.message import Message
import json  # Need json serializer for datetime handling? model_dump_json handles it.

logger = logging.getLogger(__name__)

class MessageRepository:
    def __init__(self):
        self.redis = RedisClient.get_client()

    async def save_message(self, message: Message) -> None:
        intent_key = f"intent:{message.intent_id}"
        messages_key = f"intent:{message.intent_id}:messages"
        
        # Check intent existence/TTL
        ttl = await self.redis.ttl(intent_key)
        if ttl <= 0:
            raise ValueError("Intent expired or not found")
        
        data = message.model_dump_json()
        
        # RPUSH to list
        count = await self.redis.rpush(messages_key, data)
        
        # Trim to keep density (e.g. last 100 messages)
        # "Density and honesty matter more than engagement".
        if count > 100:
            await self.redis.ltrim(messages_key, -100, -1)
            
        # Refresh TTL of messages key to match intent
        await self.redis.expire(messages_key, ttl)
        
        logger.info(f"Saved message from {message.user_id} to intent {message.intent_id}")

    async def get_messages(self, intent_id: UUID, limit: int = 50) -> list[Message]:
        messages_key = f"intent:{intent_id}:messages"
        # Get last N messages
        # lrange 0 -1 gets all. 
        # range: start, stop.
        # If we want last N: -limit, -1
        raw_list = await self.redis.lrange(messages_key, -limit, -1)
        
        return [Message.model_validate_json(m) for m in raw_list]
