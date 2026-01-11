import uuid
import logging
from fastapi import FastAPI, Request
from .config import settings
from .logging_config import configure_logging
from .storage.redis import lifespan

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

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
