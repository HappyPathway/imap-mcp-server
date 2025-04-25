"""Simple tool to test IMAP connection."""

import imaplib
from typing import Dict

def test_imap_connection(host: str, username: str, password: str) -> Dict[str, str]:
    """Test connection to an IMAP server.
    
    Args:
        host: IMAP server hostname
        username: IMAP account username 
        password: IMAP account password
        
    Returns:
        Dict containing connection status and details
    """
    try:
        # Try establishing connection
        imap = imaplib.IMAP4_SSL(host)
        
        # Try authentication
        imap.login(username, password)
        
        # Get server capabilities
        capabilities = imap.capability()[1][0].decode()
        
        # Properly close connection
        imap.logout()
        
        return {
            "status": "success",
            "message": "Successfully connected to IMAP server",
            "capabilities": capabilities
        }
        
    except imaplib.IMAP4.error as e:
        return {
            "status": "error",
            "message": f"IMAP error: {str(e)}",
            "capabilities": ""
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Connection error: {str(e)}",
            "capabilities": ""
        }
