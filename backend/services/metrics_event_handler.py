from ..core.events import IntentCreated, IntentJoined, MessagePosted, IntentFlagged
from ..core.interfaces.repositories import MetricsRepository
import logging

logger = logging.getLogger(__name__)


class MetricsEventHandler:
    """Handles domain events by logging metrics (eventual consistency)."""
    
    def __init__(self, metrics_repo: MetricsRepository):
        self.metrics_repo = metrics_repo

    async def on_intent_created(self, event: IntentCreated):
        """Log metrics when an intent is created."""
        # We need to create a minimal Intent object for the existing metrics API
        # In the future, we should change the metrics API to accept event data directly
        from ..core.models.intent import Intent
        intent = Intent(
            id=event.intent_id,
            user_id=event.user_id,
            title=event.title,
            emoji=event.emoji,
            latitude=event.latitude,
            longitude=event.longitude,
            created_at=event.timestamp
        )
        await self.metrics_repo.log_intent_creation(intent)
        logger.debug(f"Logged metrics for intent creation: {event.intent_id}")

    async def on_intent_joined(self, event: IntentJoined):
        """Log metrics when an intent is joined."""
        await self.metrics_repo.log_join(str(event.intent_id), str(event.user_id))
        logger.debug(f"Logged metrics for intent join: {event.intent_id}")

    async def on_message_posted(self, event: MessagePosted):
        """Log metrics when a message is posted."""
        await self.metrics_repo.log_message(
            str(event.intent_id),
            str(event.user_id),
            event.content_length
        )
        logger.debug(f"Logged metrics for message: {event.message_id}")

    async def on_intent_flagged(self, event: IntentFlagged):
        """Log metrics when an intent is flagged."""
        # For now, just log it. We could add specific metrics tracking for flags.
        logger.info(f"Intent {event.intent_id} flagged, new count: {event.new_flag_count}")
