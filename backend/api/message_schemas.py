from uuid import UUID
from pydantic import BaseModel

class CreateMessageRequest(BaseModel):
    content: str
