from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class Join(BaseModel):
    intent_id: UUID
    user_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
