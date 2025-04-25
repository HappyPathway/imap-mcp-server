#!/usr/bin/env python3
"""Test script for IMAP connection verification."""

import os
import sys
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    logger.debug("Starting IMAP connection test")
    
    try:
        logger.debug("Attempting to import test_connection")
        from tools.test_connection import test_imap_connection
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.debug("Python path: %s", sys.path)
        return 1

    # Get credentials from environment variables or use test values
    host = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    username = os.getenv('IMAP_USERNAME', 'test@example.com')
    password = os.getenv('IMAP_PASSWORD', 'test-password')
    
    print(f"Testing IMAP connection to {host}...")
    print(f"Username: {username}")
    print("Password: ********")
    
    try:
        logger.debug("Calling test_imap_connection function")
        result = test_imap_connection(host, username, password)
        print("\nTest Results:")
        print("-" * 50)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        if result['capabilities']:
            print("\nServer Capabilities:")
            capabilities = result['capabilities'].split()
            for cap in capabilities:
                print(f"- {cap}")
    except Exception as e:
        logger.error("Error during test execution", exc_info=True)
        print("\nError occurred during testing:")
        print("-" * 50)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
