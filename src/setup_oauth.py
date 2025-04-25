#!/usr/bin/env python3
"""Setup script for Gmail OAuth2 authentication."""

import os
import sys
import argparse
import logging

# Get the absolute path to the services directory
SERVICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services')
sys.path.insert(0, SERVICES_DIR)

from google_auth import GoogleAuth, GoogleAuthConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_oauth(credentials_path: str = None):
    """Run the OAuth2 setup process."""
    config = GoogleAuthConfig()
    if credentials_path:
        config.credentials_path = os.path.expanduser(credentials_path)
    
    auth = GoogleAuth(config)
    
    try:
        # This will trigger the OAuth2 flow
        auth.get_credentials()
        logger.info("OAuth2 setup completed successfully!")
        logger.info(f"Credentials saved to: {config.credentials_path}")
        logger.info(f"Token saved to: {config.token_path}")
        return True
    except FileNotFoundError:
        logger.error(
            f"\nNo credentials.json found at {config.credentials_path}\n"
            "\nTo set up OAuth2 authentication:\n"
            "1. Go to https://console.cloud.google.com\n"
            "2. Create a project or select an existing one\n"
            "3. Enable the Gmail API\n"
            "4. Go to Credentials\n"
            "5. Click Create Credentials > OAuth client ID\n"
            "6. Choose Desktop Application\n"
            "7. Download the credentials and save as ~/.imap-mcp/credentials.json\n"
        )
        return False
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Set up Gmail OAuth2 authentication")
    parser.add_argument(
        "--credentials",
        help="Path to credentials.json file (default: ~/.imap-mcp/credentials.json)"
    )
    
    args = parser.parse_args()
    if not setup_oauth(args.credentials):
        sys.exit(1)

if __name__ == "__main__":
    main()
