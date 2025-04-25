"""Direct IMAP connection test."""
import asyncio
import sys
import os
from aioimaplib import IMAP4_SSL

async def test_imap():
    print("Starting IMAP test...")
    print(f"Python version: {sys.version}")
    
    host = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    username = os.getenv('IMAP_USERNAME')
    password = os.getenv('IMAP_PASSWORD')
    
    print(f"\nConfiguration:")
    print(f"Server: {host}")
    print(f"Username: {username}")
    print("Password: [hidden]")
    
    try:
        print(f"\nConnecting to {host}...")
        imap = IMAP4_SSL(host)
        await imap.wait_hello_from_server()
        print("Server connection established")
        
        print("\nAttempting login...")
        response = await imap.login(username, password)
        print(f"Login response: {response}")
        
        if response.result == 'OK':
            print("\nGetting capabilities...")
            cap_response = await imap.capability()
            capabilities = cap_response.lines[0].decode().split()
            print(f"Server capabilities: {capabilities}")
            
            print("\nLogging out...")
            await imap.logout()
            print("Test completed successfully")
        else:
            print(f"\nLogin failed: {response.lines[0].decode() if response.lines else 'Unknown error'}")
            
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        if "invalid credentials" in str(e).lower():
            print("\nNote: For Gmail accounts with 2FA enabled, you need to use an App Password")
            print("You can generate one at: https://myaccount.google.com/apppasswords")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(test_imap())
