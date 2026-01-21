from typing import List
from ..core.models.intent import Intent
from ..core.interfaces.repositories import IntentRepository


class IntentQueryService:
    """Handles read-only queries for intents (CQRS pattern)."""
    
    def __init__(self, intent_repo: IntentRepository):
        self.intent_repo = intent_repo

    async def get_nearby(
        self,
        lat: float,
        lon: float,
        radius: float = 1.0,
        limit: int = 50
    ) -> List[Intent]:
        """Get intents near a location."""
        return await self.intent_repo.find_nearby(lat, lon, radius, limit)

    async def get_clusters(
        self,
        lat: float,
        lon: float,
        radius: float = 10.0
    ) -> dict:
        """Get clustered view of intents in an area."""
        clusters = await self.intent_repo.get_clusters(lat, lon, radius)
        return {"clusters": clusters}
