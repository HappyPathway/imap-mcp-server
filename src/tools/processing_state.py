"""Tool for tracking IMAP processing state."""

from typing import Dict, Optional
from datetime import datetime
import logging
from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger(__name__)

mcp = FastMCP("Processing State")

@mcp.tool()
async def get_last_processed(folder: str) -> Dict:
    """Get information about the last processed message in a folder.
    
    Args:
        folder: The name of the mail folder
        
    Returns:
        Dict containing:
        - last_message_id: ID of the last processed message
        - last_processed_date: ISO timestamp of last processing
        - is_success: Whether last processing completed successfully
        - error: Any error message from last processing
        - sync_token: IMAP sync token if supported
    """
    with get_session() as session:
        state = session.query(ProcessingState).filter_by(folder=folder).first()
        if state:
            return {
                "last_message_id": state.last_message_id,
                "last_processed_date": state.last_processed_date,
                "is_success": bool(state.last_success),
                "error": state.error_message,
                "sync_token": state.sync_token
            }
        return {
            "last_message_id": None,
            "last_processed_date": None,
            "is_success": True,
            "error": None,
            "sync_token": None
        }

@mcp.tool()
async def update_processing(folder: str, message_id: str, sync_token: Optional[str] = None, error: Optional[str] = None) -> bool:
    """Update the processing state for a folder
    
    Args:
        folder: Name of the folder being processed
        message_id: ID of the last successfully processed message
        sync_token: Optional IMAP sync token for resuming
        error: Optional error message if processing failed
        
    Returns:
        bool: True if state was updated successfully
    """
    try:
        with get_session() as session:
            state = session.query(ProcessingState).filter_by(folder=folder).first()
            if not state:
                state = ProcessingState(folder=folder)
                session.add(state)
            
            state.last_message_id = message_id
            state.last_processed_date = datetime.now().isoformat()
            state.last_success = 0 if error else 1
            state.error_message = error
            state.sync_token = sync_token
            
            return True
    except Exception as e:
        logger.error(f"Failed to update processing state: {str(e)}")
        return False
