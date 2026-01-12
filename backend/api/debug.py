from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..storage.intent_repo import IntentRepository
from ..tasks.seeder import seed_ambient_intents
from ..domain.intent import Intent

router = APIRouter()

class DebugSeedRequest(BaseModel):
    latitude: float
    longitude: float
    count: int = 3
    radius_km: float = 0.5

@router.post("/seed", response_model=list[Intent])
async def seed_intents(
    request: DebugSeedRequest,
    repo: IntentRepository = Depends()
):
    """
    Debug endpoint to manually trigger ambient intent seeding.
    """
    seeded = await seed_ambient_intents(
        repo=repo,
        lat=request.latitude,
        lon=request.longitude,
        count=request.count,
        radius_km=request.radius_km
    )
    return seeded
