from uuid import UUID
from pydantic import BaseModel

class CreateMessageRequest(BaseModel):
    user_id: UUID
    content: str
