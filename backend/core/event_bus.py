from typing import Protocol, List, Callable, Awaitable, Dict
from .events import DomainEvent
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus(Protocol):
    """Protocol for publishing and subscribing to domain events."""
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        ...
    
    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        ...


class InMemoryEventBus:
    """In-memory event bus implementation. Events are processed asynchronously."""
    
    def __init__(self):
        self._handlers: Dict[type, List[EventHandler]] = {}

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed handler to {event_type.__name__}")

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers. Errors are logged, not propagated."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for {event_type.__name__}")
            return
        
        for handler in handlers:
            try:
                await handler(event)
                logger.debug(f"Handler executed for {event_type.__name__}")
            except Exception as e:
                # Log error, don't propagate (eventual consistency)
                logger.error(f"Event handler failed for {event_type.__name__}: {e}", exc_info=True)
