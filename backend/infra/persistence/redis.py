from typing import Optional
from redis.asyncio import Redis, from_url
from contextlib import asynccontextmanager
from backend.config import settings
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _client: Optional[Redis] = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            raise RuntimeError("Redis client not initialized")
        return cls._client

    @classmethod
    async def connect(cls, redis_url: str = "redis://localhost:6379"):
        logger.info(f"Connecting to Redis at {redis_url}")
        cls._client = from_url(redis_url, encoding="utf-8", decode_responses=True)
        await cls._client.ping()
        logger.info("Connected to Redis")

    @classmethod
    async def disconnect(cls):
        if cls._client:
            logger.info("Disconnecting from Redis")
            await cls._client.close()
            cls._client = None

# Dependency
async def get_redis_client() -> Redis:
    return RedisClient.get_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine Redis URL from settings or default
    redis_url = getattr(settings, "REDIS_DSN", "redis://localhost:6379")
    await RedisClient.connect(redis_url)
    yield
    await RedisClient.disconnect()
