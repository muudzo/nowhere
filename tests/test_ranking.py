import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from backend.domain.intent import Intent
from backend.domain.ranking import calculate_score, is_visible

def make_intent(ago_seconds=0, joins=0, system=False):
    return Intent(
        id=uuid4(),
        user_id="test_user",
        title="Test Intent",
        emoji="🧪",
        latitude=0.0,
        longitude=0.0,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=ago_seconds),
        join_count=joins,
        is_system=system
    )

def test_freshness_decay():
    now = datetime.now(timezone.utc)
    
    # Fresh (0s) -> Score should include full Freshness weight (2.0)
    i1 = make_intent(ago_seconds=0)
    s1 = calculate_score(i1, dist_km=0, now=now)
    
    # Stale (12h) -> Freshness score should be ~0.5 * 2.0 = 1.0
    i2 = make_intent(ago_seconds=12*3600)
    s2 = calculate_score(i2, dist_km=0, now=now)
    
    # Dead (24h) -> Freshness score 0
    i3 = make_intent(ago_seconds=24*3600)
    s3 = calculate_score(i3, dist_km=0, now=now)
    
    print(f"S1: {s1}, S2: {s2}, S3: {s3}")
    assert s1 > s2 > s3

def test_distance_decay():
    now = datetime.now(timezone.utc)
    i = make_intent()
    
    # 0km -> full dist score (1.0)
    s1 = calculate_score(i, dist_km=0, now=now)
    
    # 0.5km -> 0.5 * 1.0 = 0.5
    s2 = calculate_score(i, dist_km=0.5, radius_km=1.0, now=now)
    
    # 1.0km -> 0
    s3 = calculate_score(i, dist_km=1.0, radius_km=1.0, now=now)
    
    assert s1 > s2 > s3
    assert s3 < s1

def test_popularity_impact():
    now = datetime.now(timezone.utc)
    
    i1 = make_intent(joins=0)
    i2 = make_intent(joins=10)
    
    s1 = calculate_score(i1, dist_km=0, now=now)
    s2 = calculate_score(i2, dist_km=0, now=now)
    
    assert s2 > s1

def test_visibility_thresholds():
    # Regular user, 0 joins -> hidden if > 0.2km
    i1 = make_intent(joins=0, system=False)
    assert is_visible(i1, 0.1) is True
    assert is_visible(i1, 0.3) is False
    
    # System intent -> always visible (within query radius)
    i2 = make_intent(joins=0, system=True)
    assert is_visible(i2, 0.3) is True
    
    # Popular intent -> visible
    i3 = make_intent(joins=5, system=False)
    assert is_visible(i3, 0.5) is True
