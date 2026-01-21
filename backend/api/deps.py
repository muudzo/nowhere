from fastapi import Request, HTTPException
from uuid import UUID

def get_current_user_id(request: Request) -> UUID:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # Should be caught by middleware normally, but defensive check
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID")

from fastapi import Depends
from redis.asyncio import Redis
from ..infra.persistence.redis import get_redis_client
from ..infra.persistence.redis import get_redis_client
from ..spam import SpamDetector
from ..infra.persistence.intent_repo import IntentRepository
from ..infra.persistence.join_repo import JoinRepository
from ..infra.persistence.message_repo import MessageRepository
from ..infra.persistence.metrics_repo import MetricsRepository
from ..services.intent_service import IntentService
from ..services.intent_command_handler import IntentCommandHandler
from ..services.intent_query_service import IntentQueryService
from ..core.clock import Clock, SystemClock

def get_clock() -> Clock:
    return SystemClock()

def get_spam_detector(redis: Redis = Depends(get_redis_client)) -> SpamDetector:
    return SpamDetector(redis)

def get_intent_service(
    intent_repo: IntentRepository = Depends(),
    join_repo: JoinRepository = Depends(),
    message_repo: MessageRepository = Depends(),
    metrics_repo: MetricsRepository = Depends(),
    spam_detector: SpamDetector = Depends(get_spam_detector),
    clock: Clock = Depends(get_clock)
) -> IntentService:
    return IntentService(
        intent_repo=intent_repo,
        join_repo=join_repo,
        message_repo=message_repo,
        metrics_repo=metrics_repo,
        spam_detector=spam_detector,
        clock=clock
    )

def get_intent_command_handler(
    intent_repo: IntentRepository = Depends(),
    join_repo: JoinRepository = Depends(),
    message_repo: MessageRepository = Depends(),
    metrics_repo: MetricsRepository = Depends(),
    spam_detector: SpamDetector = Depends(get_spam_detector)
) -> IntentCommandHandler:
    return IntentCommandHandler(
        intent_repo=intent_repo,
        join_repo=join_repo,
        message_repo=message_repo,
        metrics_repo=metrics_repo,
        spam_detector=spam_detector
    )

def get_intent_query_service(
    intent_repo: IntentRepository = Depends()
) -> IntentQueryService:
    return IntentQueryService(intent_repo=intent_repo)
