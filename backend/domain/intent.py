from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator
import re

class Intent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, max_length=50)
    emoji: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True

    @field_validator('emoji')
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        # Basic check: typically single character or combined emoji sequence. 
        # For simplicity in this commit, we limit length to a small number (e.g. 2 for simple emojis, 
        # though some can be longer). Let's go with max_length 4 to cover most standard emojis.
        # A more robust regex library "emoji" could be used, but keeping it simple as per "Prefer simplicity".
        if len(v) == 0 or len(v) > 4:
            raise ValueError('Emoji must be a single emoji character')
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
