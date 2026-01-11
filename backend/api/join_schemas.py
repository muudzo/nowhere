from uuid import UUID
from pydantic import BaseModel

class JoinRequest(BaseModel):
    user_id: UUID
