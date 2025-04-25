"""IMAP service implementation."""

import logging
from typing import Dict, List, Optional
from aioimaplib import IMAP4_SSL

logger = logging.getLogger(__name__)

class IMAPService:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.imap: Optional[IMAP4_SSL] = None
        self.capabilities: List[str] = []
        
    async def connect(self) -> bool:
        """Establish connection to IMAP server.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.imap = IMAP4_SSL(self.host)
            await self.imap.wait_hello_from_server()
            
            response = await self.imap.login(self.username, self.password)
            if response.result != 'OK':
                logger.error(f"Login failed: {response.lines[0]}")
                return False
                
            response = await self.imap.capability()
            self.capabilities = response.lines[0].decode().split()
            logger.info(f"Connected with capabilities: {self.capabilities}")
            
            return True
            
        except Exception as e:
            logger.error("Connection failed", exc_info=True)
            return False
            
    async def disconnect(self) -> None:
        """Safely disconnect from IMAP server."""
        if self.imap:
            try:
                await self.imap.logout()
                self.imap = None
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                
    async def test_connection(self) -> Dict[str, any]:
        """Test IMAP connection and return status.
        
        Returns:
            Dict with connection status and capabilities
        """
        try:
            if await self.connect():
                result = {
                    "status": "success",
                    "message": "Successfully connected to IMAP server",
                    "capabilities": self.capabilities
                }
            else:
                result = {
                    "status": "error",
                    "message": "Connection failed",
                    "capabilities": []
                }
                
            await self.disconnect()
            return result
            
        except Exception as e:
            logger.error("Test connection failed", exc_info=True)
            return {
                "status": "error",
                "message": f"Connection error: {str(e)}",
                "capabilities": []
            }
