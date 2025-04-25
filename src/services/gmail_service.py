"""Gmail API service implementation."""

import os
import base64
import logging
import email.mime.text
from typing import Optional, List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .google_auth import GoogleAuth

logger = logging.getLogger(__name__)

class GmailService:
    """Handles Gmail API operations."""
    
    def __init__(self):
        self.auth = GoogleAuth()
        self.service = None
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    async def connect(self) -> bool:
        """Initialize Gmail API service."""
        try:
            credentials = self.auth.get_credentials()
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Successfully connected to Gmail API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gmail API: {e}")
            return False

    async def list_labels(self) -> List[Dict[str, str]]:
        """Get list of all Gmail labels."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            return [{'name': label['name'], 'id': label['id']} for label in labels]
        except Exception as e:
            logger.error(f"Failed to list labels: {e}")
            return []

    async def get_messages(self, label_ids: List[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get messages from Gmail, optionally filtered by labels."""
        try:
            # Build the query
            query = {'userId': 'me', 'maxResults': max_results}
            if label_ids:
                query['labelIds'] = label_ids

            # Get message list
            results = self.service.users().messages().list(**query).execute()
            messages = results.get('messages', [])
            
            # Get full message details
            full_messages = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me', 
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = {h['name']: h['value'] for h in message['payload']['headers']}
                    
                    full_messages.append({
                        'id': message['id'],
                        'threadId': message['threadId'],
                        'labelIds': message['labelIds'],
                        'snippet': message['snippet'],
                        'subject': headers.get('Subject', ''),
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'date': headers.get('Date', '')
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg['id']}: {e}")
                    continue
                    
            return full_messages
            
        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            return []

    async def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get all messages in a thread."""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            for msg in thread['messages']:
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                messages.append({
                    'id': msg['id'],
                    'snippet': msg['snippet'],
                    'subject': headers.get('Subject', ''),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'date': headers.get('Date', '')
                })
                
            return {
                'id': thread['id'],
                'messages': messages,
                'messageCount': len(messages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            return None

    async def search_messages(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for messages using Gmail's search syntax."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                return []
                
            full_messages = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = {h['name']: h['value'] for h in message['payload']['headers']}
                    full_messages.append({
                        'id': message['id'],
                        'threadId': message['threadId'],
                        'labelIds': message['labelIds'],
                        'snippet': message['snippet'],
                        'subject': headers.get('Subject', ''),
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'date': headers.get('Date', '')
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg['id']}: {e}")
                    continue
                    
            return full_messages
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []
