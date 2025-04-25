"""Core database operations tools."""

from typing import Dict, List, Optional
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session
from ..database import get_session
from ..models import EmailMessage, EmailThread, SmartFolder, AnalyticsCache

logger = logging.getLogger(__name__)

def write_email_record(folder: str, message_id: str, metadata: Dict) -> bool:
    """Write an email record to the database."""
    try:
        with get_session() as session:
            record = session.query(EmailMessage).filter_by(
                message_id=message_id,
                folder=folder
            ).first()
            
            data = {
                "message_id": message_id,
                "folder": folder,
                "subject": metadata.get("subject", ""),
                "sender": metadata.get("sender", ""),
                "recipients": json.dumps(metadata.get("recipients", [])),
                "date": metadata.get("date", datetime.now().isoformat()),
                "thread_id": metadata.get("thread_id"),
                "references": json.dumps(metadata.get("references", [])),
                "content_preview": metadata.get("content_preview", ""),
                "importance_score": float(metadata.get("importance_score", 0.0)),
                "labels": json.dumps(metadata.get("labels", [])),
                "category": metadata.get("category"),
                "response_time": metadata.get("response_time")
            }
            
            if not record:
                record = EmailMessage(**data)
                session.add(record)
            else:
                for key, value in data.items():
                    setattr(record, key, value)
                    
            session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error writing email record: {str(e)}")
        session.rollback()
        return False

def write_thread_record(thread_id: str, messages: List[Dict]) -> bool:
    """Write a thread record to the database."""
    try:
        with get_session() as session:
            record = session.query(EmailThread).filter_by(thread_id=thread_id).first()
            
            data = {
                "thread_id": thread_id,
                "subject": messages[0].get("subject", "") if messages else "",
                "participants": json.dumps(list({msg.get("sender") for msg in messages})),
                "last_update": datetime.now().isoformat(),
                "message_count": len(messages),
                "average_response_time": sum(msg.get("response_time", 0) for msg in messages) / len(messages) if messages else 0,
                "is_active": 1,
                "importance_score": sum(msg.get("importance_score", 0) for msg in messages) / len(messages) if messages else 0,
                "category": messages[0].get("category") if messages else None,
                "labels": json.dumps(messages[0].get("labels", [])) if messages else "[]"
            }
            
            if not record:
                record = EmailThread(**data)
                session.add(record)
            else:
                for key, value in data.items():
                    setattr(record, key, value)
                    
            session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error writing thread record: {str(e)}")
        session.rollback()
        return False

def write_folder_record(folder_data: Dict) -> bool:
    """Write a smart folder record to the database."""
    try:
        with get_session() as session:
            record = session.query(SmartFolder).filter_by(name=folder_data["name"]).first()
            
            data = {
                "name": folder_data["name"],
                "description": folder_data["description"],
                "rules": json.dumps(folder_data.get("rules", [])),
                "created_at": datetime.now().isoformat(),
                "last_applied": datetime.now().isoformat(),
                "message_count": folder_data.get("message_count", 0),
                "is_active": 1,
                "priority": folder_data.get("priority", 0)
            }
            
            if not record:
                record = SmartFolder(**data)
                session.add(record)
            else:
                for key, value in data.items():
                    setattr(record, key, value)
                    
            session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error writing folder record: {str(e)}")
        session.rollback()
        return False

def write_analytics_record(key: str, data: Dict, expires_in_minutes: int = 60) -> bool:
    """Write an analytics record to the database."""
    try:
        with get_session() as session:
            record = session.query(AnalyticsCache).filter_by(cache_key=key).first()
            
            now = datetime.now()
            expires_at = now + timedelta(minutes=expires_in_minutes)
            
            data = {
                "cache_key": key,
                "data": json.dumps(data),
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "type": data.get("type", "general")
            }
            
            if not record:
                record = AnalyticsCache(**data)
                session.add(record)
            else:
                for key, value in data.items():
                    setattr(record, key, value)
                    
            session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error writing analytics record: {str(e)}")
        session.rollback()
        return False

def read_email_record(folder: str, message_id: str) -> Optional[Dict]:
    """Read an email record from the database."""
    try:
        with get_session() as session:
            record = session.query(EmailMessage).filter_by(
                message_id=message_id,
                folder=folder
            ).first()
            
            if record:
                return {
                    "message_id": record.message_id,
                    "folder": record.folder,
                    "subject": record.subject,
                    "sender": record.sender,
                    "recipients": json.loads(record.recipients),
                    "date": record.date,
                    "thread_id": record.thread_id,
                    "references": json.loads(record.references),
                    "content_preview": record.content_preview,
                    "importance_score": record.importance_score,
                    "labels": json.loads(record.labels),
                    "category": record.category,
                    "response_time": record.response_time
                }
            return None
            
    except Exception as e:
        logger.error(f"Error reading email record: {str(e)}")
        return None

def read_thread_record(thread_id: str) -> Optional[Dict]:
    """Read a thread record from the database."""
    try:
        with get_session() as session:
            record = session.query(EmailThread).filter_by(thread_id=thread_id).first()
            
            if record:
                return {
                    "thread_id": record.thread_id,
                    "subject": record.subject,
                    "participants": json.loads(record.participants),
                    "last_update": record.last_update,
                    "message_count": record.message_count,
                    "average_response_time": record.average_response_time,
                    "is_active": record.is_active,
                    "importance_score": record.importance_score,
                    "category": record.category,
                    "labels": json.loads(record.labels)
                }
            return None
            
    except Exception as e:
        logger.error(f"Error reading thread record: {str(e)}")
        return None
