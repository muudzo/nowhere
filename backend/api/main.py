from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from typing import AsyncGenerator

from backend.config import Settings, get_settings
from backend.infrastructure.redis.repo import create_redis
from backend.infrastructure.postgres.repo import create_postgres_pool
from backend.application.handlers import create_activity_handler, join_activity_handler, post_message_handler

app = FastAPI(title="Nowhere - Hybrid Backend")


@app.on_event("startup")
async def startup() -> None:
    settings = get_settings()
    app.state.redis = await create_redis(settings.REDIS_DSN)
    app.state.pg = await create_postgres_pool(settings.POSTGRES_DSN)


@app.on_event("shutdown")
async def shutdown() -> None:
    try:
        await app.state.redis.close()
    except Exception:
        pass
    try:
        await app.state.pg.close()
    except Exception:
        pass


def get_redis():
    return app.state.redis


def get_pg():
    return app.state.pg


@app.get("/health")
async def health():
    # simple readiness probe
    try:
        await app.state.redis.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="redis down")
    try:
        await app.state.pg.fetchrow("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="postgres down")
    return JSONResponse({"status": "ok"})


@app.post("/activities")
async def create_activity(payload: dict, redis=Depends(get_redis), pg=Depends(get_pg)):
    # thin handler delegates to application layer
    return await create_activity_handler(payload, redis, pg)


@app.post("/activities/{activity_id}/join")
async def join_activity(activity_id: str, payload: dict, redis=Depends(get_redis), pg=Depends(get_pg)):
    return await join_activity_handler(activity_id, payload, redis, pg)


@app.post("/activities/{activity_id}/messages")
async def post_message(activity_id: str, payload: dict, redis=Depends(get_redis), pg=Depends(get_pg)):
    return await post_message_handler(activity_id, payload, redis, pg)
