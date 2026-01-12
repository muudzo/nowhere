from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from ..domain.intent import Intent
from ..domain.message import Message
from ..storage.intent_repo import IntentRepository
from ..storage.join_repo import JoinRepository
from ..storage.message_repo import MessageRepository
from ..spam import SpamDetector
from .deps import get_current_user_id, get_spam_detector
from .limiter import RateLimiter, DynamicRateLimiter
from .message_schemas import CreateMessageRequest
from .join_schemas import JoinRequest
from .schemas import NearbyResponse, CreateIntentRequest, ClusterResponse

router = APIRouter()


from fastapi import BackgroundTasks
from ..storage.metrics_repo import MetricsRepository

@router.post("/", response_model=Intent, status_code=201, dependencies=[Depends(DynamicRateLimiter("create_intent", 5, 3600))])
async def create_intent(
    intent_request: CreateIntentRequest, 
    background_tasks: BackgroundTasks,
    repo: IntentRepository = Depends(),
    metrics: MetricsRepository = Depends(),
    spam: SpamDetector = Depends(get_spam_detector),
    user_id: str = Depends(get_current_user_id)
):
    # Spam Check
    await spam.check(intent_request.title, str(user_id))

    # Create intent domain object
    try:
        intent = Intent(
            title=intent_request.title,
            emoji=intent_request.emoji,
            latitude=intent_request.latitude,
            longitude=intent_request.longitude,
            user_id=str(user_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await repo.save_intent(intent)
    
    # Log Metric
    background_tasks.add_task(metrics.log_intent_creation, intent)
    
    return intent

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

@router.get("/clusters", response_model=ClusterResponse)
async def get_intent_clusters(
    lat: float,
    lon: float,
    radius: float = 10.0,
    repo: IntentRepository = Depends()
):
    clusters = await repo.get_clusters(lat, lon, radius)
    return {"clusters": clusters}

@router.post("/{intent_id}/join", status_code=200, dependencies=[Depends(RateLimiter("join", 20, 3600))])
async def join_intent(
    intent_id: UUID, 
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    repo: JoinRepository = Depends(),
    metrics: MetricsRepository = Depends()
):
    try:
        joined = await repo.save_join(intent_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    if not joined:
        return {"joined": False, "intent_id": intent_id, "message": "Already joined"}
    
    # Log Metric
    background_tasks.add_task(metrics.log_join, str(intent_id), str(user_id))
        
    return {"joined": True, "intent_id": intent_id}

@router.post("/{intent_id}/messages", response_model=Message, dependencies=[Depends(RateLimiter("message", 100, 3600))])
async def post_message(
    intent_id: UUID, 
    request: CreateMessageRequest, 
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    join_repo: JoinRepository = Depends(),
    repo: MessageRepository = Depends(),
    metrics: MetricsRepository = Depends(),
    spam: SpamDetector = Depends(get_spam_detector)
):
    # Spam Check
    await spam.check(request.content, str(user_id))

    # Check if joined
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
    
    # Log Metric
    background_tasks.add_task(metrics.log_message, str(intent_id), str(user_id), len(message.content))
        
    return message

@router.post("/{intent_id}/flag", status_code=200)
async def flag_intent(intent_id: UUID, repo: IntentRepository = Depends()):
    new_flags = await repo.flag_intent(intent_id)
    return {"id": intent_id, "flags": new_flags}
