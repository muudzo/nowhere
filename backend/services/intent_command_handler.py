from uuid import UUID
from ..core.command_handler import CommandHandler
from ..core.commands import CreateIntent, JoinIntent, PostMessage, FlagIntent
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.interfaces.repositories import IntentRepository, JoinRepository, MessageRepository, MetricsRepository
from ..core.exceptions import DomainError
from ..spam import SpamDetector


class IntentCommandHandler:
    """Handles write commands for the intent domain."""
    
    def __init__(
        self,
        intent_repo: IntentRepository,
        join_repo: JoinRepository,
        message_repo: MessageRepository,
        metrics_repo: MetricsRepository,
        spam_detector: SpamDetector
    ):
        self.intent_repo = intent_repo
        self.join_repo = join_repo
        self.message_repo = message_repo
        self.metrics_repo = metrics_repo
        self.spam_detector = spam_detector

    async def handle_create_intent(self, cmd: CreateIntent) -> Intent:
        """Handle creation of a new intent."""
        # Spam Check
        await self.spam_detector.check(cmd.title, cmd.user_id)

        # Create Domain Object
        intent = Intent(
            title=cmd.title,
            emoji=cmd.emoji,
            latitude=cmd.latitude,
            longitude=cmd.longitude,
            user_id=cmd.user_id,
            created_at=cmd.timestamp
        )

        # Persistence
        await self.intent_repo.save_intent(intent)
        
        # Metrics (will be replaced with events in Commit 3)
        await self.metrics_repo.log_intent_creation(intent)
        
        return intent

    async def handle_join_intent(self, cmd: JoinIntent) -> bool:
        """Handle joining an intent."""
        joined = await self.join_repo.save_join(cmd.intent_id, cmd.user_id)
        if joined:
            await self.metrics_repo.log_join(str(cmd.intent_id), str(cmd.user_id))
        return joined

    async def handle_post_message(self, cmd: PostMessage) -> Message:
        """Handle posting a message to an intent."""
        # Spam Check
        await self.spam_detector.check(cmd.content, str(cmd.user_id))

        # Check membership
        if not await self.join_repo.is_member(cmd.intent_id, cmd.user_id):
            raise DomainError("Must join intent to message")

        message = Message(
            intent_id=cmd.intent_id,
            user_id=cmd.user_id,
            content=cmd.content,
            created_at=cmd.timestamp
        )
        
        await self.message_repo.save_message(message)
        await self.metrics_repo.log_message(str(cmd.intent_id), str(cmd.user_id), len(cmd.content))
        
        return message

    async def handle_flag_intent(self, cmd: FlagIntent) -> int:
        """Handle flagging an intent."""
        return await self.intent_repo.flag_intent(cmd.intent_id)
