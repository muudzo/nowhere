from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.exceptions import IntentNotFound, DomainError, InvalidAction
from .deps import get_current_user_id, get_intent_service
from .limiter import RateLimiter, DynamicRateLimiter
from .message_schemas import CreateMessageRequest
from .join_schemas import JoinRequest
from .schemas import NearbyResponse, CreateIntentRequest, ClusterResponse
from ..services.intent_service import IntentService

router = APIRouter()

@router.post("/", response_model=Intent, status_code=201, dependencies=[Depends(DynamicRateLimiter("create_intent", 5, 3600))])
async def create_intent(
    intent_request: CreateIntentRequest, 
    service: IntentService = Depends(get_intent_service),
    user_id: str = Depends(get_current_user_id)
):
    try:
        intent = await service.create_intent(
            title=intent_request.title,
            emoji=intent_request.emoji,
            latitude=intent_request.latitude,
            longitude=intent_request.longitude,
            user_id=str(user_id)
        )
        return intent
    except ValueError as e:
         raise HTTPException(status_code=422, detail=str(e))

@router.get("/nearby", response_model=NearbyResponse)
async def find_nearby_intents(
    lat: float, 
    lon: float, 
    radius: float = 1.0, 
    limit: int = 50,
    service: IntentService = Depends(get_intent_service)
):
    intents = await service.get_nearby_intents(lat, lon, radius, limit)
    
    response = NearbyResponse(intents=intents, count=len(intents))
    if not intents:
        response.message = "It's quiet here. Start something?"
        
    return response

@router.get("/clusters", response_model=ClusterResponse)
async def get_intent_clusters(
    lat: float,
    lon: float,
    radius: float = 10.0,
    service: IntentService = Depends(get_intent_service)
):
    return await service.get_clusters(lat, lon, radius)

@router.post("/{intent_id}/join", status_code=200, dependencies=[Depends(RateLimiter("join", 20, 3600))])
async def join_intent(
    intent_id: UUID, 
    user_id: UUID = Depends(get_current_user_id),
    service: IntentService = Depends(get_intent_service)
):
    try:
        result = await service.join_intent(intent_id, user_id)
        if not result["joined"]:
             return {"joined": False, "intent_id": intent_id, "message": "Already joined"}
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{intent_id}/messages", response_model=Message, dependencies=[Depends(RateLimiter("message", 100, 3600))])
async def post_message(
    intent_id: UUID, 
    request: CreateMessageRequest, 
    user_id: UUID = Depends(get_current_user_id),
    service: IntentService = Depends(get_intent_service)
):
    try:
        message = await service.post_message(intent_id, user_id, request.content)
        return message
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DomainError as e:
        # Map domain errors
        if "Must join" in str(e):
             raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{intent_id}/flag", status_code=200)
async def flag_intent(
    intent_id: UUID, 
    service: IntentService = Depends(get_intent_service)
):
    return await service.flag_intent(intent_id)
