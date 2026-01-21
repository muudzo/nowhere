from typing import Protocol
from .commands import CreateIntent, JoinIntent, PostMessage, FlagIntent
from .models.intent import Intent
from .models.message import Message


class CommandHandler(Protocol):
    """Protocol for handling write commands."""
    
    async def handle_create_intent(self, cmd: CreateIntent) -> Intent:
        """Handle creation of a new intent."""
        ...
    
    async def handle_join_intent(self, cmd: JoinIntent) -> bool:
        """Handle joining an intent. Returns True if joined, False if already member."""
        ...
    
    async def handle_post_message(self, cmd: PostMessage) -> Message:
        """Handle posting a message to an intent."""
        ...
    
    async def handle_flag_intent(self, cmd: FlagIntent) -> int:
        """Handle flagging an intent. Returns new flag count."""
        ...
