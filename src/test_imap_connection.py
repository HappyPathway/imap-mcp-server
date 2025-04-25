#!/usr/bin/env python3
"""Simple IMAP connection tester with debug mode."""

import os
import sys
import imaplib
import traceback

def test_connection(host: str, username: str, password: str, debug: bool = False) -> dict:
    """Test IMAP connection with optional debug output.
    
    Args:
        host: IMAP server hostname
        username: IMAP account username
        password: IMAP account password
        debug: Enable debug output
        
    Returns:
        Dictionary with test results
    """
    if debug:
        sys.stderr.write(f"Debug: Testing connection to {host}\n")
        sys.stderr.flush()
    
    try:
        # Try establishing connection
        if debug:
            sys.stderr.write("Debug: Creating IMAP SSL connection\n")
            sys.stderr.flush()
        
        imap = imaplib.IMAP4_SSL(host)
        imap.debug = 4  # Enable IMAP debug output
        
        # Try authentication
        if debug:
            sys.stderr.write("Debug: Attempting login\n")
            sys.stderr.flush()
            
        imap.login(username, password)
        
        # Get server capabilities
        if debug:
            sys.stderr.write("Debug: Getting capabilities\n")
            sys.stderr.flush()
            
        capabilities = imap.capability()[1][0].decode()
        
        # Properly close connection
        if debug:
            sys.stderr.write("Debug: Closing connection\n")
            sys.stderr.flush()
            
        imap.logout()
        
        return {
            "status": "success",
            "message": "Successfully connected to IMAP server",
            "capabilities": capabilities
        }
        
    except Exception as e:
        if debug:
            sys.stderr.write(f"Debug: Error occurred - {type(e).__name__}: {str(e)}\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}",
            "capabilities": ""
        }

def main():
    # Get credentials from environment variables
    host = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    username = os.getenv('IMAP_USERNAME', 'test@example.com')
    password = os.getenv('IMAP_PASSWORD', 'test-password')
    
    print("IMAP Connection Test")
    print("=" * 50)
    print(f"Server: {host}")
    print(f"Username: {username}")
    print("Password: ********")
    print("-" * 50)
    
    result = test_connection(host, username, password, debug=True)
    
    print("\nTest Results:")
    print("=" * 50)
    print(f"Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    
    if result['capabilities']:
        print("\nServer Capabilities:")
        for cap in result['capabilities'].split():
            print(f"- {cap}")
    
    return 0 if result['status'] == 'success' else 1

if __name__ == "__main__":
    sys.exit(main())
