from typing import Protocol, List, Any
from .events import DomainEvent
from .interfaces.repositories import IntentRepository, JoinRepository, MessageRepository


class UnitOfWork(Protocol):
    """Protocol for atomic operations across repositories."""
    
    intent_repo: IntentRepository
    join_repo: JoinRepository
    message_repo: MessageRepository
    
    async def __aenter__(self) -> "UnitOfWork":
        """Start the transaction."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End the transaction. Rollback on exception, commit otherwise."""
        ...

    async def commit(self) -> None:
        """Commit all changes."""
        ...

    async def rollback(self) -> None:
        """Rollback all changes."""
        ...

    def collect_event(self, event: DomainEvent) -> None:
        """Collect a domain event to be published after commit."""
        ...

    def get_events(self) -> List[DomainEvent]:
        """Get collected events."""
        ...
