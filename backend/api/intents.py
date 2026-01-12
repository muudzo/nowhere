from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from ..domain.intent import Intent
from ..domain.message import Message
from ..storage.intent_repo import IntentRepository
from ..storage.join_repo import JoinRepository
from ..storage.message_repo import MessageRepository
from .deps import get_current_user_id
from .limiter import RateLimiter
from .message_schemas import CreateMessageRequest
from .join_schemas import JoinRequest
from .schemas import NearbyResponse

router = APIRouter(prefix="/intents", tags=["intents"])

class CreateIntentRequest(BaseModel):
    title: str
    emoji: str
    latitude: float
    longitude: float


@router.post("/", response_model=Intent, status_code=201, dependencies=[Depends(RateLimiter("create_intent", 5, 3600))])
async def create_intent(
    request: CreateIntentRequest, 
    repo: IntentRepository = Depends(),
    user_id: str = Depends(get_current_user_id)
):
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
async def find_nearby_intents(
    lat: float, 
    lon: float, 
    radius: float = 1.0, 
    limit: int = 50,
    repo: IntentRepository = Depends()
):
    intents = await repo.find_nearby(lat, lon, radius, limit)
    
    response = NearbyResponse(intents=intents, count=len(intents))
    if not intents:
        response.message = "It's quiet here. Start something?"
        
    return response

from .join_schemas import JoinRequest
from ..storage.join_repo import JoinRepository
from .deps import get_current_user_id

@router.post("/{intent_id}/join", status_code=200, dependencies=[Depends(RateLimiter("join", 20, 3600))])
async def join_intent(
    intent_id: UUID, 
    user_id: UUID = Depends(get_current_user_id),
    repo: JoinRepository = Depends()
):
    try:
        joined = await repo.save_join(intent_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    if not joined:
        return {"joined": False, "intent_id": intent_id, "message": "Already joined"}
        
    return {"joined": True, "intent_id": intent_id}

from .message_schemas import CreateMessageRequest
from ..domain.message import Message
from ..storage.message_repo import MessageRepository

@router.get("/{intent_id}/messages", response_model=list[Message])
async def get_messages(
    intent_id: UUID, 
    limit: int = 50,
    repo: MessageRepository = Depends()
):
    return await repo.get_messages(intent_id, limit)

@router.post("/{intent_id}/messages", response_model=Message, dependencies=[Depends(RateLimiter("message", 100, 3600))])
async def post_message(
    intent_id: UUID, 
    request: CreateMessageRequest, 
    user_id: UUID = Depends(get_current_user_id),
    join_repo: JoinRepository = Depends(),
    repo: MessageRepository = Depends()
):
    # Check if joined
    
    # We don't have a direct "is_member" check, but save_join works essentially.
    # However we want to check WITHOUT SIDE EFFECTS if possible?
    # Or just require join.
    # MVP: Check SCARD or SISMEMBER. We need SISMEMBER.
    # Let's add is_member to JoinRepo or just assume client joined.
    # But "enforce join permissions".
    if not await join_repo.is_member(intent_id, user_id):
         raise HTTPException(status_code=403, detail="Must join intent to message")

    try:
        message = Message(
            intent_id=intent_id,
            user_id=user_id,
            content=request.content
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    try:
        await repo.save_message(message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    return message

@router.post("/{intent_id}/flag", status_code=200)
async def flag_intent(intent_id: UUID, repo: IntentRepository = Depends()):
    new_flags = await repo.flag_intent(intent_id)
    return {"id": intent_id, "flags": new_flags}
