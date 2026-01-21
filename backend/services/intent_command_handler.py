from uuid import UUID, uuid4
from ..core.command_handler import CommandHandler
from ..core.commands import CreateIntent, JoinIntent, PostMessage, FlagIntent
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.interfaces.repositories import IntentRepository, JoinRepository, MessageRepository
from ..core.exceptions import DomainError
from ..core.events import IntentCreated, IntentJoined, MessagePosted, IntentFlagged
from ..core.event_bus import EventBus
from ..spam import SpamDetector


class IntentCommandHandler:
    """Handles write commands for the intent domain."""
    
    def __init__(
        self,
        intent_repo: IntentRepository,
        join_repo: JoinRepository,
        message_repo: MessageRepository,
        event_bus: EventBus,
        spam_detector: SpamDetector
    ):
        self.intent_repo = intent_repo
        self.join_repo = join_repo
        self.message_repo = message_repo
        self.event_bus = event_bus
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
        
        # Emit Event (replaces direct metrics call)
        event = IntentCreated(
            event_id=uuid4(),
            timestamp=cmd.timestamp,
            intent_id=intent.id,
            user_id=intent.user_id or "",
            title=intent.title,
            emoji=intent.emoji,
            latitude=intent.latitude,
            longitude=intent.longitude
        )
        await self.event_bus.publish(event)
        
        return intent

    async def handle_join_intent(self, cmd: JoinIntent) -> bool:
        """Handle joining an intent."""
        joined = await self.join_repo.save_join(cmd.intent_id, cmd.user_id)
        if joined:
            event = IntentJoined(
                event_id=uuid4(),
                timestamp=cmd.timestamp,
                intent_id=cmd.intent_id,
                user_id=cmd.user_id
            )
            await self.event_bus.publish(event)
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
        
        # Emit Event
        event = MessagePosted(
            event_id=uuid4(),
            timestamp=cmd.timestamp,
            message_id=message.id,
            intent_id=cmd.intent_id,
            user_id=cmd.user_id,
            content_length=len(cmd.content)
        )
        await self.event_bus.publish(event)
        
        return message

    async def handle_flag_intent(self, cmd: FlagIntent) -> int:
        """Handle flagging an intent."""
        new_flag_count = await self.intent_repo.flag_intent(cmd.intent_id)
        
        # Emit Event
        event = IntentFlagged(
            event_id=uuid4(),
            timestamp=cmd.timestamp,
            intent_id=cmd.intent_id,
            new_flag_count=new_flag_count
        )
        await self.event_bus.publish(event)
        
        return new_flag_count
