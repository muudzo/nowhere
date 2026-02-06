from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from backend.domain.models import Activity, Attendee, Message, Join
from backend.infrastructure.redis.repo import RedisActivityRepo
from backend.infrastructure.postgres.repo import PostgresVenueRepo
from backend.infrastructure.uow import UnitOfWork
from backend.config import get_settings


settings = get_settings()


async def create_activity_handler(payload: Dict[str, Any], redis, pg):
    # payload decides spontaneous or venue activity
    activity = Activity(
        id=uuid4(),
        type=payload.get("type", "spontaneous"),
        venue_id=payload.get("venue_id"),
        organizer_id=payload.get("organizer_id"),
        title=payload.get("title", "Untitled"),
        metadata=payload.get("metadata", {}),
        created_at=datetime.utcnow(),
    )

    repo = RedisActivityRepo(redis, ttl=settings.REDIS_TTL_SECONDS)
    async with UnitOfWork(redis=redis, pg=pg) as uow:
        await repo.save(activity)
        # optionally persist small index to Postgres if venue-backed
        if activity.venue_id:
            vrepo = PostgresVenueRepo(pg)
            # ensure venue exists (thin check)
            venue = await vrepo.get(activity.venue_id)
            if not venue:
                raise Exception("venue missing")
    return {"id": str(activity.id)}


async def join_activity_handler(activity_id: str, payload: Dict[str, Any], redis, pg):
    attendee = Attendee(id=uuid4(), display_name=payload.get("display_name"), device_id=payload.get("device_id"))
    # create join record in Redis
    from backend.infrastructure.redis.repo import RedisJoinRepo

    jrepo = RedisJoinRepo(redis, ttl=settings.REDIS_TTL_SECONDS)
    join = Join(id=uuid4(), activity_id=activity_id, attendee_id=attendee.id, joined_at=datetime.utcnow())
    async with UnitOfWork(redis=redis, pg=pg) as uow:
        await jrepo.save(join)
    return {"join_id": str(join.id)}


async def post_message_handler(activity_id: str, payload: Dict[str, Any], redis, pg):
    msg = Message(id=uuid4(), activity_id=activity_id, attendee_id=payload.get("attendee_id"), body=payload.get("body"), sent_at=datetime.utcnow())
    from backend.infrastructure.redis.repo import RedisMessageRepo

    mrepo = RedisMessageRepo(redis, ttl=settings.REDIS_TTL_SECONDS)
    await mrepo.save(msg)
    return {"message_id": str(msg.id)}
