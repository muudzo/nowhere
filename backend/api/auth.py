from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID, uuid4
from ..auth.jwt import create_access_token
from ..domain.intent import Intent # Just for example import correctness if needed logic elsewhere

router = APIRouter()

class HandshakeRequest(BaseModel):
    # Ideally client sends their generated UUID if they have one but no JWT yet
    anon_id: str | None = None 

class HandshakeResponse(BaseModel):
    access_token: str
    token_type: str
    anon_id: str

@router.post("/handshake", response_model=HandshakeResponse)
async def handshake(request: HandshakeRequest):
    """
    Exchange an anonymous ID (or get a new one) for a signed JWT.
    """
    user_id = request.anon_id
    if not user_id:
        user_id = str(uuid4())
    else:
        # Validate UUID format
        try:
            UUID(user_id)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Create JWT
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "anon_id": user_id
    }
