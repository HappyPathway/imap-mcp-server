# Gmail IMAP Integration Guide

## Overview

This document describes how to properly use Python's `imaplib` with Gmail in our IMAP MCP server implementation.

## Key Implementation Details

### Connection and Authentication

For Gmail, always use IMAP4_SSL (port 993) instead of standard IMAP4. Gmail requires SSL/TLS connections:

```python
import imaplib
import ssl

def create_connection():
    # Create SSL context with secure defaults
    context = ssl.create_default_context()

    # Connect to Gmail's IMAP server
    imap = imaplib.IMAP4_SSL(
        host='imap.gmail.com',
        ssl_context=context
    )
    return imap

```

### Best Practices

1. **Error Handling**:

   - Always check return types from IMAP commands
   - First element is status ('OK' or 'NO')
   - Second element contains the actual data

2. **Message Selection**:

   - Use UIDs instead of message numbers
   - Message numbers change after EXPUNGE operations
   - UIDs remain stable for message identification

3. **Resource Management**:

   - Use context managers (with statements) when possible
   - Always close connections properly
   - Sequence: CLOSE -> LOGOUT -> connection shutdown

4. **Gmail-Specific Folders**:
   - 'INBOX' - Main inbox
   - '[Gmail]/All Mail' - All messages
   - '[Gmail]/Sent Mail' - Sent messages
   - '[Gmail]/Trash' - Deleted items
   - '[Gmail]/Drafts' - Draft messages

### Common Operations

1. **Listing Folders**:

```python
typ, data = imap.list()
if typ == 'OK':
    for folder in data:
        print(folder.decode())
```

2. **Selecting a Mailbox**:

```python
typ, data = imap.select('INBOX')
if typ == 'OK':
    num_messages = int(data[0])
```

3. **Searching Messages**:

```python
# Search for all messages from last 24 hours
typ, messages = imap.search(None, 'SINCE', '1d')
```

4. **Fetching Messages**:

```python
# Fetch message by UID
typ, msg_data = imap.uid('FETCH', uid, '(RFC822)')
```

## Gmail App-Specific Passwords

For our IMAP MCP server:

1. Enable 2-Step Verification in Google Account
2. Generate an App Password for the application
3. Use the App Password instead of the regular Google account password

## Error Handling

Common Gmail IMAP errors and their handling:

1. `AUTHENTICATIONFAILED`: Invalid credentials or access not allowed
2. `[ALERT] Please log in via your web browser`: Security restrictions
3. `[ALERT] Too many simultaneous connections`: Connection limit reached

Handle these with appropriate error messages and retry logic where applicable.

## Security Considerations

1. Always use SSL/TLS connections
2. Store credentials securely
3. Implement connection timeouts
4. Monitor for failed authentication attempts
5. Log security-relevant events

## Implementation in IMAP MCP Server

Our server implementation in `email_service.py` follows these best practices by:

- Using aioimaplib for async operations
- Implementing proper error handling
- Managing connections safely
- Using UIDs for message tracking
- Supporting Gmail-specific folder structures

For detailed implementation examples, see our `services/email_service.py` file.
