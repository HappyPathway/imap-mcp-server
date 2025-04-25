"""Database models for IMAP MCP Server."""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from database import Base

class EmailMessage(Base):
    __tablename__ = 'email_messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String, nullable=False)
    folder = Column(String, nullable=False)
    subject = Column(String)
    sender = Column(String)
    recipients = Column(Text)  # JSON string
    date = Column(String)
    thread_id = Column(String)
    references = Column(Text)  # JSON string
    content_preview = Column(Text)
    importance_score = Column(Float, default=0.0)
    labels = Column(Text)  # JSON string
    category = Column(String)
    response_time = Column(Float)

class EmailThread(Base):
    __tablename__ = 'email_threads'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String, nullable=False, unique=True)
    subject = Column(String)
    participants = Column(Text)  # JSON string
    last_update = Column(String)
    message_count = Column(Integer, default=0)
    average_response_time = Column(Float)
    is_active = Column(Boolean, default=True)
    importance_score = Column(Float, default=0.0)
    category = Column(String)
    labels = Column(Text)  # JSON string

class SmartFolder(Base):
    __tablename__ = 'smart_folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    rules = Column(Text)  # JSON string
    created_at = Column(String)
    last_applied = Column(String)
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)

class ProcessingState(Base):
    __tablename__ = 'processing_states'
    
    id = Column(Integer, primary_key=True)
    folder = Column(String, nullable=False, unique=True)
    last_message_id = Column(String)
    last_processed_date = Column(String)
    last_success = Column(Boolean, default=True)
    error_message = Column(Text)
    sync_token = Column(String)

class AnalyticsCache:
    def __init__(self, key: str, data: dict, timestamp: float):
        self.key = key
        self.data = data
        self.timestamp = timestamp

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if the cached data has expired"""
        import time
        current_time = time.time()
        return current_time - self.timestamp > ttl_seconds

    @staticmethod
    def create(key: str, data: dict) -> 'AnalyticsCache':
        """Create a new cache entry with current timestamp"""
        import time
        return AnalyticsCache(key, data, time.time())
