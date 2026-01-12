from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for user_id in cookies
        # Priority 1: Header (Device-anchored identity)
        user_id = request.headers.get("X-Nowhere-Identity")

        # Priority 2: Cookie (Browser/Legacy fallback)
        if not user_id:
            user_id = request.cookies.get("user_id")

        # Validation / Generation
        try:
            if user_id:
                # Validate valid UUID
                uuid_obj = uuid.UUID(user_id)
                user_id = str(uuid_obj)
            else:
                raise ValueError("No ID")
        except ValueError:
            user_id = str(uuid.uuid4())

        # Attach to request state
        request.state.user_id = user_id
        
        response = await call_next(request)
        
        # Always refresh/set cookie for web context
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=400 * 24 * 60 * 60, # 400 days
            httponly=True,
            samesite="lax"
        )
        
        return response
