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
