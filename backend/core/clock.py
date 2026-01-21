from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Protocol for time acquisition. Enables deterministic testing."""
    
    def now(self) -> datetime:
        """Return the current time as an aware datetime in UTC."""
        ...


class SystemClock:
    """Production clock that returns the actual current time."""
    
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock:
    """Test clock that returns a frozen timestamp."""
    
    def __init__(self, frozen_time: datetime):
        if frozen_time.tzinfo is None:
            raise ValueError("FixedClock requires timezone-aware datetime")
        self._frozen_time = frozen_time
    
    def now(self) -> datetime:
        return self._frozen_time
