from typing import List, Optional
from pydantic import BaseModel
from ..domain.intent import Intent

class NearbyResponse(BaseModel):
    intents: List[Intent]
    count: int
    message: Optional[str] = None
