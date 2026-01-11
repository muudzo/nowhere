from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from ..domain.intent import Intent
from ..storage.intent_repo import IntentRepository

router = APIRouter(prefix="/intents", tags=["intents"])

class CreateIntentRequest(BaseModel):
    title: str
    emoji: str
    latitude: float
    longitude: float

@router.post("/", response_model=Intent, status_code=201)
async def create_intent(request: CreateIntentRequest):
    repo = IntentRepository()
    # Create intent domain object
    # Note: Validation happens in Intent init
    try:
        intent = Intent(
            title=request.title,
            emoji=request.emoji,
            latitude=request.latitude,
            longitude=request.longitude
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await repo.save_intent(intent)
    return intent

from .schemas import NearbyResponse

@router.get("/nearby", response_model=NearbyResponse)
async def find_nearby_intents(lat: float, lon: float, radius: float = 1.0, limit: int = 50):
    repo = IntentRepository()
    intents = await repo.find_nearby(lat, lon, radius, limit)
    
    response = NearbyResponse(intents=intents, count=len(intents))
    if not intents:
        response.message = "It's quiet here. Start something?"
        
    return response

from .join_schemas import JoinRequest
from ..storage.join_repo import JoinRepository

@router.post("/{intent_id}/join", status_code=200)
async def join_intent(intent_id: UUID, request: JoinRequest):
    repo = JoinRepository()
    try:
        joined = await repo.save_join(intent_id, request.user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {"joined": joined, "intent_id": intent_id}
