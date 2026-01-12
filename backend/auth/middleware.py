from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from .jwt import decode_access_token
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = None
        
        # Priority 1: Authorization Header (JWT)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                user_id = payload["sub"]
                # logger.debug(f"Authenticated via JWT: {user_id}")

        # Priority 2: X-Nowhere-Identity Header (Device-anchored identity)
        if not user_id:
            user_id = request.headers.get("X-Nowhere-Identity")

        # Priority 3: Cookie (Browser/Legacy fallback)
        if not user_id:
            user_id = request.cookies.get("user_id")

        # Validation / Generation
        try:
            if user_id:
                # Validate valid UUID
                uuid_obj = uuid.UUID(user_id)
                user_id = str(uuid_obj)
            else:
                user_id = str(uuid.uuid4())
                # If generated here, it's a weak identity (no persistence guarantee unless cookie works)
        except ValueError:
            user_id = str(uuid.uuid4())

        # Attach to request state
        request.state.user_id = user_id
        
        response = await call_next(request)
        
        # Always refresh/set cookie for web context (legacy support)
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=400 * 24 * 60 * 60, # 400 days
            httponly=True,
            samesite="lax"
        )
        
        return response
