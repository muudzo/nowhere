from backend.core.models.ranking import calculate_score

# Provide a simple compatibility wrapper for is_visible which exists
# as an instance method on Intent in core.models.intent

def is_visible(intent, distance_km: float) -> bool:
    return intent.is_visible(distance_km)

__all__ = ["calculate_score", "is_visible"]
