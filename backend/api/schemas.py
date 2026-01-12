from typing import List, Optional
from pydantic import BaseModel
from ..domain.intent import Intent

class CreateIntentRequest(BaseModel):
    title: str
    emoji: str
    latitude: float
    longitude: float

class NearbyResponse(BaseModel):
    intents: List[Intent]
    count: int
    message: Optional[str] = None

class ClusterItem(BaseModel):
    geohash: str
    latitude: float
    longitude: float
    count: int

class ClusterResponse(BaseModel):
    clusters: List[ClusterItem]
