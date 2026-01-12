import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .config import settings
from .logging_config import configure_logging
from .storage.redis import lifespan as redis_lifespan, RedisClient
from .storage.db import init_db
from .api.intents import router as intents_router
from .api.debug import router as debug_router
from .api.auth import router as auth_router
from .auth.middleware import AuthMiddleware

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine Redis URL from settings or default
    redis_url = getattr(settings, "redis_url", "redis://localhost:6379")
    await RedisClient.connect(redis_url)
    
    # Init DB (fire and log error if fail)
    await init_db()
    
    yield
    await RedisClient.disconnect()

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:8082", "http://localhost:8083", "http://192.168.0.12:8081", "*"], # Add common Expo ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intents_router, prefix="/intents", tags=["intents"])
app.include_router(debug_router, prefix="/debug", tags=["debug"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request started: {request.method} {request.url} - RequestID: {request_id}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Request completed: {request.method} {request.url} - RequestID: {request_id}")
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok", "app_name": settings.app_name}
