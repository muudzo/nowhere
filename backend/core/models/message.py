from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    user_id: UUID
    content: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        # "Ephemeral" utility, keep messages concise.
        if len(v) > 500:
            raise ValueError('Message content too long (max 500 chars)')
        return v
