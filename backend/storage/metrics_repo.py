from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal
from .models import IntentMetric, JoinMetric, MessageMetric
from ..domain.intent import Intent
import logging

logger = logging.getLogger(__name__)

class MetricsRepository:
    async def log_intent_creation(self, intent: Intent):
        try:
            async with AsyncSessionLocal() as session:
                metric = IntentMetric(
                    intent_id=str(intent.id),
                    user_id=intent.user_id,
                    title=intent.title,
                    emoji=intent.emoji,
                    latitude=intent.latitude,
                    longitude=intent.longitude,
                    created_at=intent.created_at,
                    is_system=intent.is_system
                )
                session.add(metric)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log intent metric: {e}")

    async def log_join(self, intent_id: str, user_id: str):
        try:
            async with AsyncSessionLocal() as session:
                metric = JoinMetric(
                    intent_id=str(intent_id),
                    user_id=str(user_id)
                )
                session.add(metric)
                await session.commit()
        except Exception as e:
             logger.error(f"Failed to log join metric: {e}")

    async def log_message(self, intent_id: str, user_id: str, content_length: int):
        try:
            async with AsyncSessionLocal() as session:
                metric = MessageMetric(
                     intent_id=str(intent_id),
                     user_id=str(user_id),
                     content_length=content_length
                )
                session.add(metric)
                await session.commit()
        except Exception as e:
             logger.error(f"Failed to log message metric: {e}")
