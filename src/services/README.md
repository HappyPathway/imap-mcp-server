# Email Services for IMAP MCP Server

This directory contains service components for handling email operations through IMAP.

## EmailService

The `EmailService` class provides a robust interface for interacting with IMAP servers, with a focus on Gmail compatibility. It implements connection management, folder operations, and message handling with comprehensive error handling.

### Key Features

1. **Robust Connection Management**
   - SSL/TLS secure connections
   - Async and sync fallback support
   - Automatic reconnection for transient failures
   - Graceful timeout handling
   - Connection state verification

2. **Error Handling**
   - Specific error type detection and handling
   - Granular logging at appropriate levels
   - Recovery mechanisms for common failures
   - Connection reset capabilities
   - Safe resource cleanup

3. **Message Operations**
   - Stable message identification with UIDs
   - Folder/label management
   - Message fetching with pagination
   - Message moving between folders
   - Secure message content extraction

## Usage Guidelines

### Connection Lifecycle

Always manage connections properly in application code:

```python
# Create service
email_service = EmailService()

# Connect with error handling
try:
    connected = await email_service.connect()
    if not connected:
        # Handle connection failure
        logger.error("Failed to connect to IMAP server")
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Error connecting to IMAP server: {e}")

# When finished, always disconnect
finally:
    await email_service.disconnect()
```

For multiple operations, use the async context manager:

```python
async with EmailService() as email_service:
    # Do operations with the service
    messages = await email_service.get_messages("INBOX", 10)
    # Process messages
```

### Error Handling Best Practices

1. Always check connection state before operations
2. Use try/except blocks around IMAP operations
3. Handle specific error types differently
4. Implement retry logic for transient failures
5. Log appropriate context for debugging

## Implementation Notes

1. **Gmail Compatibility**: The service includes specific handling for Gmail's IMAP implementation quirks.
2. **Connection Resilience**: Implements timeouts and retries for robustness.
3. **Performance**: Uses batch operations where possible for efficiency.
4. **Security**: Proper credential handling and secure connection defaults.