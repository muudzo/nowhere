from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Intent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    emoji: str
    latitude: float
    longitude: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
