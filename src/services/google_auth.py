"""Google OAuth2 authentication for Gmail IMAP."""

import os
import base64
import pickle
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pydantic import BaseModel

# If modifying scopes, delete the token.pickle file.
SCOPES = ['https://mail.google.com/']

logger = logging.getLogger(__name__)

class GoogleAuthConfig(BaseModel):
    """Configuration for Google OAuth2 authentication."""
    credentials_path: str = os.path.expanduser('~/.imap-mcp/credentials.json')
    token_path: str = os.path.expanduser('~/.imap-mcp/token.pickle')


class GoogleAuth:
    """Handles Google OAuth2 authentication for Gmail IMAP."""
    
    def __init__(self, config: Optional[GoogleAuthConfig] = None):
        self.config = config or GoogleAuthConfig()
        self.creds: Optional[Credentials] = None
        os.makedirs(os.path.dirname(self.config.token_path), exist_ok=True)
        
    def load_saved_credentials(self) -> bool:
        """Load saved credentials from pickle file."""
        try:
            if os.path.exists(self.config.token_path):
                with open(self.config.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
                return bool(self.creds and not self.creds.expired)
        except Exception as e:
            logger.warning(f"Failed to load saved credentials: {e}")
        return False
    
    def save_credentials(self) -> None:
        """Save credentials to pickle file."""
        try:
            with open(self.config.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing or running auth flow if needed."""
        if self.load_saved_credentials():
            if not self.creds.expired:
                return self.creds
        
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                self.save_credentials()
                return self.creds
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
        
        if not os.path.exists(self.config.credentials_path):
            raise FileNotFoundError(
                f"No credentials.json found at {self.config.credentials_path}. "
                "Download OAuth 2.0 Client ID credentials from Google Cloud Console "
                "and save as credentials.json"
            )
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.config.credentials_path,
                SCOPES,
                redirect_uri='http://localhost:0'  # Dynamic port allocation
            )
            self.creds = flow.run_local_server(port=0)
            self.save_credentials()
            return self.creds
        except Exception as e:
            raise RuntimeError(f"Failed to get credentials: {e}")

    def get_imap_auth_string(self) -> str:
        """Get IMAP XOAUTH2 authentication string."""
        if not self.creds:
            self.get_credentials()
            
        if not self.creds:
            raise RuntimeError("Failed to obtain credentials")
            
        auth_string = f'user={self.creds.client_id}\\1auth=Bearer {self.creds.token}\\1\\1'
        return base64.b64encode(auth_string.encode()).decode()
