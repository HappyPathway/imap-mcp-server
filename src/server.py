"""Gmail MCP Server implementation."""

from functools import wraps
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any, AsyncIterator
import asyncio
import logging
import json
import os
import ssl
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, AsyncIterator
import asyncio
import logging
import json
import os
import ssl
from datetime import datetime, timedelta
import google.generativeai as genai
from google.cloud import storage
from google.auth import default
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from analytics import EmailAnalytics
from database import get_session, init_db
from models import EmailMessage, EmailThread, SmartFolder, ProcessingState
from services.gmail_service import GmailService

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IMAPConfig(BaseModel):
    host: str = Field(default="imap.gmail.com")
    credentials_path: str = Field(
        default="~/.imap-mcp/credentials.json",
        description="Path to the OAuth2 credentials file"
    )
    token_path: str = Field(
        default="~/.imap-mcp/token.pickle",
        description="Path to save the OAuth2 token"
    )

class GeminiConfig(BaseModel):
    apiKey: str

class GCSConfig(BaseModel):
    project_id: str = Field(default=None, description="GCP project ID. If None, will use ADC project")
    bucket_name: str = Field(..., description="GCS bucket containing the database")

class AnalyticsConfig(BaseModel):
    batchSize: int = 50
    cacheDuration: int = 60
    enableThreadAnalysis: bool = True
    enablePriorityScoring: bool = True

class FilterRule(BaseModel):
    field: str = Field(description="Email field to apply the rule to", enum=["subject", "from", "to", "body"])
    operator: str = Field(description="Type of match to perform", enum=["contains", "equals", "startswith", "endswith"])
    value: str = Field(description="Value to match against")

class BatchCriteria(BaseModel):
    sender: Optional[str] = Field(default=None, description="Filter by sender email")
    subject: Optional[str] = Field(default=None, description="Filter by subject line")
    date_from: Optional[str] = Field(default=None, description="Filter by date (ISO format)")
    date_to: Optional[str] = Field(default=None, description="Filter by date (ISO format)")
    has_attachments: Optional[bool] = Field(default=None, description="Filter by attachment presence")

# Initialize global services
gmail_service: Optional[GmailService] = None
storage_client = None
bucket = None
analytics = None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Server lifespan handler."""
    global gmail_service, storage_client, bucket, analytics
    
    logger.info("Starting IMAP MCP Server...")
    
    try:
        # Initialize GCS and download database
        credentials, project = default()
        gcs_config = GCSConfig(
            project_id=os.getenv("GCP_PROJECT", project),
            bucket_name=os.getenv("GCS_BUCKET")
        )
        if not gcs_config.bucket_name:
            raise ValueError("GCS_BUCKET environment variable must be set")
        
        storage_client = storage.Client(project=gcs_config.project_id, credentials=credentials)
        bucket = storage_client.bucket(gcs_config.bucket_name)
        logger.info(f"Connected to GCS bucket: {gcs_config.bucket_name}")
        
        # Handle database initialization and sync
        db_blob = bucket.blob("database.sqlite")
        db_exists_locally = os.path.exists("database.sqlite")
        db_exists_in_gcs = db_blob.exists()
        
        logger.info(f"Database status - Local: {'exists' if db_exists_locally else 'missing'}, GCS: {'exists' if db_exists_in_gcs else 'missing'}")
        
        if db_exists_locally:
            # We have a local database, try to sync from GCS if available
            if db_exists_in_gcs:
                try:
                    # Backup local DB before overwriting
                    if os.path.exists("database.sqlite"):
                        os.replace("database.sqlite", "database.sqlite.backup")
                    db_blob.download_to_filename("database.sqlite")
                    logger.info("Successfully synced database from GCS")
                except Exception as e:
                    logger.warning(f"Failed to sync from GCS, using local database: {e}")
                    # Restore backup if download failed
                    if os.path.exists("database.sqlite.backup"):
                        os.replace("database.sqlite.backup", "database.sqlite")
            else:
                # Local DB exists but not in GCS - upload it
                try:
                    db_blob.upload_from_filename("database.sqlite")
                    logger.info("Uploaded existing local database to GCS")
                except Exception as e:
                    logger.warning(f"Failed to upload local database to GCS: {e}")
        
        elif db_exists_in_gcs:
            # No local DB but exists in GCS - download it
            try:
                db_blob.download_to_filename("database.sqlite")
                logger.info("Downloaded database from GCS")
            except Exception as e:
                logger.error(f"Failed to download database from GCS: {e}")
                # If we can't download, we need to create new
                db_exists_in_gcs = False
        
        if not db_exists_locally and not db_exists_in_gcs:
            # No database anywhere - initialize new one
            logger.info("First time run - initializing new database")
            init_db()  # Create tables
            try:
                db_blob.upload_from_filename("database.sqlite")
                logger.info("Uploaded initial database to GCS")
            except Exception as e:
                logger.warning(f"Failed to upload initial database to GCS: {e}")
        
        # Create Gmail service instance
        gmail_service = GmailService()
        logger.info("Created Gmail service instance")
        
        # Initialize analytics
        analytics = EmailAnalytics()
        
        # Initialize Gemini
        gemini_config = GeminiConfig(
            apiKey=os.getenv("GEMINI_API_KEY")
        )
        if not gemini_config.apiKey:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        genai.configure(api_key=gemini_config.apiKey)
        logger.info("Gemini API configured successfully")
        
        yield
    finally:
        try:
            # Upload database back to GCS if it exists
            if os.path.exists("database.sqlite"):
                bucket.blob("database.sqlite").upload_from_filename("database.sqlite")
                logger.info("Uploaded database to GCS")
        except Exception as e:
            logger.error(f"Failed to upload database to GCS: {e}")
        
        # Close the Gmail service
        if gmail_service:
            # Gmail API doesn't need explicit disconnect
            logger.info("Gmail service cleaned up")

# Create FastMCP server instance with lifespan
mcp = FastMCP(
    name="IMAP MCP Server",
    instructions="IMAP email server with AI-powered analysis capabilities",
    lifespan=server_lifespan
)

async def ensure_connection():
    """Ensure Gmail API connection is active"""
    global gmail_service
    try:
        if not gmail_service:
            gmail_service = GmailService()
            logger.info("Created new Gmail service instance")
        
        # Gmail API doesn't maintain a persistent connection like IMAP
        # Instead, we validate our credentials are working
        labels = await gmail_service.list_labels()
        if not labels:
            logger.warning("Gmail API connection test returned no labels")
            # Force reconnection
            gmail_service = GmailService()
            await gmail_service.connect()
            
        logger.debug("Gmail API connection verified")
        return True
    except Exception as e:
        logger.error(f"Gmail API connection error: {str(e)}")
        raise RuntimeError(f"Failed to connect to Gmail API: {str(e)}")

def with_connection(func):
    """Decorator to ensure IMAP connection is active"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await ensure_connection()
        return await func(*args, **kwargs)
    return wrapper

@mcp.tool()
async def test_connection(ctx: Context) -> Dict[str, Any]:
    """Test the Gmail API connection using OAuth2 credentials."""
    try:
        if await gmail_service.connect():
            labels = await gmail_service.list_labels()
            return {
                "status": "success",
                "message": "Successfully connected to Gmail API",
                "labels": labels
            }
        else:
            raise RuntimeError("Failed to connect to Gmail API")
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Connection error: {error_msg}")
        return {
            "status": "error",
            "message": f"Connection error: {error_msg}",
            "labels": []
        }

@mcp.tool()
@with_connection
async def list_labels(ctx: Context) -> Dict[str, Any]:
    """List all available labels in Gmail."""
    try:
        labels = await gmail_service.list_labels()
        return {
            "status": "success",
            "labels": labels
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to list labels: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "labels": []
        }

@mcp.tool()
@with_connection
async def search_emails(
    ctx: Context,
    mailbox: str = "INBOX",
    criteria: str = "ALL",
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """Search emails in a mailbox using IMAP search criteria."""
    try:
        messages = await gmail_service.search_messages(criteria, limit=limit)
        return {
            "status": "success",
            "total": len(messages),
            "offset": offset,
            "limit": limit,
            "messages": messages
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Search failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "messages": []
        }

@mcp.tool()
@with_connection
async def get_email(ctx: Context, mailbox: str, message_id: str) -> Dict[str, Any]:
    """Fetch complete email content by message ID."""
    try:
        message = await email_service.get_message_by_uid(mailbox, message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found in {mailbox}")
        return {
            "status": "success",
            "message_id": message_id,
            "content": message
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to fetch email: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "content": None
        }

@mcp.tool()
@with_connection
async def analyze_inbox(ctx: Context, days: int = 7) -> Dict[str, Any]:
    """Analyze email patterns and provide insights from the inbox."""
    try:
        messages = await gmail_service.get_messages(['INBOX'], max_results=100)  # Gmail API uses label IDs
        results = await analytics.analyze_patterns(
            messages, 
            enable_thread_analysis=True,
            enable_priority_scoring=True
        )
        return {
            "status": "success",
            **results
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Analysis failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def get_total_messages(ctx: Context) -> Dict[str, Any]:
    """Get the total number of messages in the inbox."""
    try:
        messages = await gmail_service.search_messages('in:inbox', max_results=1)
        total = messages.get('resultSizeEstimate', 0) if isinstance(messages, dict) else 0
        return {
            "status": "success",
            "total_messages": total
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to get message count: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def analyze_inbox_state(
    ctx: Context,
    max_messages: int = Field(default=100, description="Maximum number of messages to analyze")
) -> Dict[str, Any]:
    """Perform a comprehensive analysis of inbox state.
    
    Args:
        max_messages: Maximum number of messages to analyze (default: 100)
    """
    try:
        # 1. Get labels and their counts
        labels = await gmail_service.list_labels()
        
        # 2. Get messages from inbox with specified limit
        messages = await gmail_service.get_messages(['INBOX'], max_results=max_messages)
        
        # Get total message count for context
        total_result = await get_total_messages(ctx)
        total_messages = total_result.get('total_messages', 0)
        
        # 3. Process messages for analysis
        sender_groups = {}
        domain_groups = {}
        email_types = {
            'newsletters': 0,
            'notifications': 0,
            'personal': 0,
            'business': 0,
            'automated': 0
        }
        attachments_count = 0

        for msg in messages:
            # Sender analysis
            sender = msg.get('from', '')
            sender_groups[sender] = sender_groups.get(sender, 0) + 1
            
            # Domain analysis
            domain = sender.split('@')[-1] if '@' in sender else 'unknown'
            domain_groups[domain] = domain_groups.get(domain, 0) + 1
            
            # Check for attachments
            if msg.get('attachments'):
                attachments_count += 1
            
            # Classify email type
            subject = msg.get('subject', '').lower()
            if any(word in subject for word in ['subscribe', 'newsletter', 'digest']):
                email_types['newsletters'] += 1
            elif any(word in subject for word in ['notification', 'alert', 'update']):
                email_types['notifications'] += 1
            elif 'noreply@' in sender or 'no-reply@' in sender:
                email_types['automated'] += 1
            elif any(domain in sender for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']):
                email_types['personal'] += 1
            else:
                email_types['business'] += 1

        return {
            "status": "success",
            "analysis_scope": {
                "messages_analyzed": len(messages),
                "total_messages": total_messages,
                "coverage_percentage": round((len(messages) / total_messages * 100) if total_messages > 0 else 0, 2)
            },
            "labels": labels,
            "sender_analysis": {
                "top_senders": dict(sorted(sender_groups.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_domains": dict(sorted(domain_groups.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "email_types": email_types,
            "attachments_info": {
                "messages_with_attachments": attachments_count,
                "percentage": round((attachments_count / len(messages)) * 100 if messages else 0, 2)
            }
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Analysis failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def move_message(
    ctx: Context,
    uid: str = Field(description="Unique identifier of the email message"),
    from_folder: str = Field(description="Source folder containing the message"),
    to_folder: str = Field(description="Destination folder to move the message to")
) -> Dict[str, Any]:
    """Move a message from one folder to another"""
    try:
        result = await email_service.move_message(uid, from_folder, to_folder)
        return {
            "status": "success",
            "moved": result
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to move message: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def create_smart_folder(
    ctx: Context,
    name: str = Field(description="Name of the smart folder to create"),
    rules: List[FilterRule] = Field(description="List of filtering rules for this folder")
) -> Dict[str, Any]:
    """Create a smart folder with specified filtering rules"""
    try:
        with get_session() as session:
            smart_folder = SmartFolder(name=name, rules=json.dumps(rules))
            session.add(smart_folder)
            session.commit()
            
            # Try to create the folder in IMAP if needed
            await email_service.create_folder(name)
            
            return {
                "status": "success",
                "name": name,
                "rules": rules
            }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to create smart folder: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def batch_process(
    ctx: Context,
    folder: str = Field(description="The folder to process emails from"),
    action: str = Field(description="Action to perform", enum=["move", "delete", "label", "mark_read", "mark_unread"]),
    filter_criteria: BatchCriteria = Field(description="Criteria to filter emails by")
) -> Dict[str, Any]:
    """Process multiple emails in batch based on criteria"""
    try:
        results = await email_service.batch_process(folder, action, filter_criteria)
        return {
            "status": "success",
            **results
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Batch processing failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
async def search_messages(ctx: Context, query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search Gmail messages using Gmail's powerful search syntax.
    
    Args:
        query: Gmail search query (e.g. 'from:someone@example.com has:attachment')
        max_results: Maximum number of messages to return
    """
    try:
        messages = await email_service.search_messages(query, max_results)
        return {
            "status": "success",
            "messages": messages
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Search failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "messages": []
        }

@mcp.tool()
async def get_thread(ctx: Context, thread_id: str) -> Dict[str, Any]:
    """Get all messages in a Gmail thread.
    
    Args:
        thread_id: The ID of the thread to retrieve
    """
    try:
        thread = await email_service.get_thread(thread_id)
        if thread:
            return {
                "status": "success",
                "thread": thread
            }
        else:
            raise ValueError(f"Thread {thread_id} not found")
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to get thread: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "thread": None
        }

@mcp.tool()
async def get_messages(ctx: Context, label_ids: Optional[List[str]] = None, max_results: int = 10) -> Dict[str, Any]:
    """Get Gmail messages, optionally filtered by labels.
    
    Args:
        label_ids: Optional list of Gmail label IDs to filter by
        max_results: Maximum number of messages to return
    """
    try:
        messages = await email_service.get_messages(label_ids, max_results)
        return {
            "status": "success",
            "messages": messages
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to get messages: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "messages": []
        }

@mcp.tool()
@with_connection
async def migrate_email_to_gcs(
    ctx: Context,
    uid: str = Field(description="Unique identifier of the email message"),
    folder: str = Field(description="Folder containing the message"),
    gcs_prefix: str = Field(default="emails", description="GCS prefix/folder to store the email in")
) -> Dict[str, Any]:
    """Migrate an email message to Google Cloud Storage."""
    try:
        # Get the full message using Gmail API
        message = await gmail_service.get_message(uid)
        if not message:
            raise ValueError(f"Message {uid} not found")
            
        # Create a unique path for this email
        timestamp = message.get("date", "").replace(" ", "_").replace(":", "-")
        base_path = f"{gcs_prefix}/{timestamp}_{uid}"
        
        # Store email metadata and content
        email_data = {
            "uid": uid,
            "folder": folder,
            "subject": message.get("subject", ""),
            "from": message.get("from", ""),
            "to": message.get("to", ""),
            "date": message.get("date", ""),
            "body": message.get("body", ""),
            "has_attachments": bool(message.get("attachments", []))
        }
        
        # Upload email data as JSON
        json_blob = bucket.blob(f"{base_path}/email.json")
        json_blob.upload_from_string(
            json.dumps(email_data, indent=2),
            content_type="application/json"
        )
        
        results = {
            "email_json": json_blob.name,
            "attachments": []
        }
        
        # Upload any attachments
        for attachment in message.get("attachments", []):
            att_name = attachment.get("filename", "unnamed")
            att_data = attachment.get("data", b"")
            att_type = attachment.get("content_type", "application/octet-stream")
            
            # Create safe filename
            safe_name = "".join(c for c in att_name if c.isalnum() or c in ".-_")
            att_blob = bucket.blob(f"{base_path}/attachments/{safe_name}")
            
            # Upload attachment
            att_blob.upload_from_string(
                att_data,
                content_type=att_type
            )
            results["attachments"].append(att_blob.name)
        
        logger.info(f"Successfully migrated email {uid} to GCS: {base_path}")
        return {
            "status": "success",
            **results
        }
        
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to migrate email to GCS: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@mcp.tool()
@with_connection
async def get_folder_summary(
    ctx: Context,
    folder: str = Field(description="The folder to get summary statistics for")
) -> Dict[str, Any]:
    """Get summary statistics for a folder"""
    try:
        messages = await email_service.get_messages(folder, limit=100)
        results = await analytics.get_folder_summary(messages)
        return {
            "status": "success",
            **results
        }
    except Exception as e:
        error_msg = str(e)
        await ctx.error(f"Failed to get folder summary: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
