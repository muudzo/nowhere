from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for user_id in cookies
        user_id = request.cookies.get("user_id")
        
        # If not present, generate one (but we don't set it on request.state yet - that's Commit 28)
        new_user = False
        if not user_id:
            user_id = str(uuid.uuid4())
            new_user = True
            
        # Proceed
        response = await call_next(request)
        
        # Set cookie if it was new
        if new_user:
            # 400 days expiry (approx forever)
            response.set_cookie(
                key="user_id", 
                value=user_id, 
                max_age=34560000, 
                httponly=True,
                samesite="lax"
            )
            
        return response
