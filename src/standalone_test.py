#!/usr/bin/env python3
"""Standalone IMAP connection test script."""

import os
import sys
import imaplib
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imap():
    logger.debug("Starting IMAP test")
    
    # Get credentials from environment
    host = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    username = os.getenv('IMAP_USERNAME', 'test@example.com')
    password = os.getenv('IMAP_PASSWORD', 'test-password')
    
    logger.info(f"Testing connection to {host}")
    logger.info(f"Using username: {username}")
    
    try:
        logger.debug("Creating IMAP SSL connection")
        imap = imaplib.IMAP4_SSL(host)
        
        logger.debug("Attempting login")
        imap.login(username, password)
        
        logger.debug("Getting server capabilities")
        capabilities = imap.capability()[1][0].decode()
        
        logger.debug("Logging out")
        imap.logout()
        
        print("\nConnection Test Results")
        print("=" * 50)
        print(f"Status: SUCCESS")
        print(f"Server: {host}")
        print("\nServer Capabilities:")
        for cap in capabilities.split():
            print(f"  - {cap}")
            
    except imaplib.IMAP4.error as e:
        print("\nConnection Test Results")
        print("=" * 50)
        print(f"Status: FAILED (IMAP Error)")
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print("\nConnection Test Results")
        print("=" * 50)
        print(f"Status: FAILED (Unexpected Error)")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(test_imap())
