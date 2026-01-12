from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone
from .db import Base

class IntentMetric(Base):
    __tablename__ = "metrics_intents"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    user_id = Column(String, index=True, nullable=True)
    title = Column(String)
    emoji = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    is_system = Column(Boolean, default=False)

# We can add JoinMetric, MessageMetric later or now.
# Prompt said "intent_metrics, message_metrics, join_metrics".

class JoinMetric(Base):
    __tablename__ = "metrics_joins"
    
    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    user_id = Column(String, index=True)
    joined_at = Column(DateTime, default=datetime.now(timezone.utc))

class MessageMetric(Base):
    __tablename__ = "metrics_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    user_id = Column(String, index=True)
    content_length = Column(Integer)
    sent_at = Column(DateTime, default=datetime.now(timezone.utc))
