from uuid import UUID, uuid4
from ..core.command_handler import CommandHandler
from ..core.commands import CreateIntent, JoinIntent, PostMessage, FlagIntent
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.unit_of_work import UnitOfWork
from ..core.exceptions import DomainError
from ..core.events import IntentCreated, IntentJoined, MessagePosted, IntentFlagged
from ..spam import SpamDetector


class IntentCommandHandler:
    """Handles write commands for the intent domain using Unit of Work."""
    
    def __init__(
        self,
        uow: UnitOfWork,
        spam_detector: SpamDetector
    ):
        self.uow = uow
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

        async with self.uow:
            # Persistence (Write)
            await self.uow.intent_repo.save_intent(intent)
            
            # Event Collection
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
            self.uow.collect_event(event)
            
            # Commit
            await self.uow.commit()
        
        return intent

    async def handle_join_intent(self, cmd: JoinIntent) -> bool:
        """Handle joining an intent."""
        async with self.uow:
            # Atomic Join (returns promise in pipeline, optimistic logic)
            # If Lua fail (intent missing), commit will raise.
            joined = await self.uow.join_repo.save_join(cmd.intent_id, cmd.user_id)
            
            # We assume success if we reach here in pipeline mode, 
            # or handle logic if synchronous.
            # In UoW, we proceed to collect event.
            # Ideally events should be conditional on 'joined' but 'save_join' is idempotent-ish or decisive.
            
            event = IntentJoined(
                event_id=uuid4(),
                timestamp=cmd.timestamp,
                intent_id=cmd.intent_id,
                user_id=cmd.user_id
            )
            self.uow.collect_event(event)

            await self.uow.commit()
            
        return True # Return true if no exception raised during commit

    async def handle_post_message(self, cmd: PostMessage) -> Message:
        """Handle posting a message to an intent."""
        # Spam Check
        await self.spam_detector.check(cmd.content, str(cmd.user_id))

        async with self.uow:
            # Check membership (Read via Reader)
            # This works inside 'async with uow' because repos are initialized.
            if not await self.uow.join_repo.is_member(cmd.intent_id, cmd.user_id):
                raise DomainError("Must join intent to message")

            message = Message(
                intent_id=cmd.intent_id,
                user_id=cmd.user_id,
                content=cmd.content,
                created_at=cmd.timestamp
            )
            
            # Persistence (Write)
            await self.uow.message_repo.save_message(message)
            
            # Event Collection
            event = MessagePosted(
                event_id=uuid4(),
                timestamp=cmd.timestamp,
                message_id=message.id,
                intent_id=cmd.intent_id,
                user_id=cmd.user_id,
                content_length=len(cmd.content)
            )
            self.uow.collect_event(event)
            
            await self.uow.commit()
        
        return message

    async def handle_flag_intent(self, cmd: FlagIntent) -> int:
        """Handle flagging an intent."""
        async with self.uow:
            # Atomic Flag (Write)
            new_flag_count = await self.uow.intent_repo.flag_intent(cmd.intent_id)
            
            # Event Collection
            event = IntentFlagged(
                event_id=uuid4(),
                timestamp=cmd.timestamp,
                intent_id=cmd.intent_id,
                new_flag_count=new_flag_count # In pipeline, this is 0 or ignored. 
            )
            self.uow.collect_event(event)
            
            await self.uow.commit()
        
        # We can't return the real flag count in pipeline mode accurately without resolving result.
        # But we return what we got (likely 0 or logic assumption).
        return new_flag_count
