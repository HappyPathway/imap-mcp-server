"""Database operation tools for IMAP MCP Server."""

from typing import Dict, List, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from ..database import get_session
from ..models import EmailMessage, EmailThread, SmartFolder, AnalyticsCache

def cache_email_message(folder: str, message_id: str, metadata: Dict) -> bool:
    """Cache email message metadata in database."""
    try:
        with get_session() as session:
            cached_message = session.query(EmailMessage).filter_by(
                message_id=message_id,
                folder=folder
            ).first()
            
            message_data = {
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
            
            if not cached_message:
                cached_message = EmailMessage(**message_data)
                session.add(cached_message)
            else:
                for key, value in message_data.items():
                    setattr(cached_message, key, value)
                    
            return True
            
    except Exception as e:
        logger.error(f"Error caching email message: {str(e)}")
        return False

def cache_email_thread(thread_id: str, messages: List[Dict]) -> bool:
    """Cache email thread analysis in database."""
    try:
        with get_session() as session:
            thread_data = {
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
            
            thread = session.query(EmailThread).filter_by(thread_id=thread_id).first()
            if not thread:
                thread = EmailThread(**thread_data)
                session.add(thread)
            else:
                for key, value in thread_data.items():
                    setattr(thread, key, value)
                    
            return True
            
    except Exception as e:
        logger.error(f"Error caching email thread: {str(e)}")
        return False

def cache_smart_folder(folder_data: Dict) -> bool:
    """Cache smart folder suggestion in database."""
    try:
        with get_session() as session:
            folder = session.query(SmartFolder).filter_by(name=folder_data["name"]).first()
            
            folder_record = {
                "name": folder_data["name"],
                "description": folder_data["description"],
                "rules": json.dumps(folder_data["rules"]),
                "created_at": datetime.now().isoformat(),
                "last_applied": datetime.now().isoformat(),
                "message_count": folder_data.get("message_count", 0),
                "is_active": 1,
                "priority": folder_data.get("priority", 0)
            }
            
            if not folder:
                folder = SmartFolder(**folder_record)
                session.add(folder)
            else:
                for key, value in folder_record.items():
                    setattr(folder, key, value)
                    
            return True
            
    except Exception as e:
        logger.error(f"Error caching smart folder: {str(e)}")
        return False

def cache_analytics_result(key: str, data: Dict, expires_in_minutes: int = 60) -> bool:
    """Cache analytics result with expiration."""
    try:
        with get_session() as session:
            now = datetime.now()
            expires_at = now + timedelta(minutes=expires_in_minutes)
            
            cache_entry = session.query(AnalyticsCache).filter_by(cache_key=key).first()
            if not cache_entry:
                cache_entry = AnalyticsCache(
                    cache_key=key,
                    data=json.dumps(data),
                    created_at=now.isoformat(),
                    expires_at=expires_at.isoformat(),
                    type=data.get("type", "general")
                )
                session.add(cache_entry)
            else:
                cache_entry.data = json.dumps(data)
                cache_entry.created_at = now.isoformat()
                cache_entry.expires_at = expires_at.isoformat()
                cache_entry.type = data.get("type", "general")
                
            return True
            
    except Exception as e:
        logger.error(f"Error caching analytics result: {str(e)}")
        return False
