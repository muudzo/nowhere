from datetime import datetime, timezone
from math import log1p
from .intent import Intent

# Weights
W_DIST = 1.0
W_FRESH = 2.0
W_POP = 0.5



def calculate_score(
    intent: Intent, 
    dist_km: float, 
    radius_km: float = 1.0, 
    now: datetime = None
) -> float:
    """
    Calculates Liveness Score based on Distance, Freshness (Time Decay), and Popularity.
    """
    if now is None:
        now = datetime.now(timezone.utc)
        
    # 1. Distance Score (0 to 1, 1 is closest)
    # Normalize: 1 - (dist / radius)
    dist_score = max(0, 1.0 - (dist_km / radius_km))
    
    # 2. Freshness Score (Decay over 24h)
    created_at = intent.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    age_seconds = (now - created_at).total_seconds()
    # 24 hours (86400s) decay window
    freshness_score = max(0, 1.0 - (age_seconds / 86400.0))
    
    # 3. Popularity Score (Logarithmic)
    # log1p(0) = 0
    # log1p(10) ~ 2.4
    pop_score = log1p(intent.join_count)
    
    total_score = (W_DIST * dist_score) + (W_FRESH * freshness_score) + (W_POP * pop_score)
    
    return total_score
