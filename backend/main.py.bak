import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .config import settings
from .core.logging import configure_logging
from .core.exceptions import DomainError, IntentNotFound, InvalidAction, IntentExpired, SpamDetected
from .infra.persistence.redis import lifespan as redis_lifespan, RedisClient
from .infra.persistence.db import init_db
from .api.intents import router as intents_router
from .api.debug import router as debug_router
from .api.auth import router as auth_router
from .auth.middleware import AuthMiddleware

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine Redis URL from settings or default
    redis_url = getattr(settings, "REDIS_DSN", "redis://localhost:6379")
    await RedisClient.connect(redis_url)
    
    # Init DB (fire and log error if fail)
    await init_db()
    
    yield
    await RedisClient.disconnect()

app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "http://10.10.0.69:8081",  # User's current IP
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+",
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

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    logger.warning(f"Domain Error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(IntentNotFound)
async def intent_not_found_handler(request: Request, exc: IntentNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Intent not found"},
    )
    
@app.exception_handler(SpamDetected)
async def spam_handler(request: Request, exc: SpamDetected):
    return JSONResponse(
        status_code=400, # or 429? 400 for content spam
        content={"detail": str(exc)},
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME}
