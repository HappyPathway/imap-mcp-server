# Gmail MCP Server API Documentation

The `imap-mcp-server` provides a set of tools and endpoints for managing and analyzing Gmail accounts.

## Tools

### `test_connection`

- **Description**: Test the Gmail API connection using OAuth2 credentials.
- **Returns**: A list of Gmail labels if the connection is successful.

### `list_labels`

- **Description**: List all available labels in your Gmail account.
- **Returns**: A dictionary of label names and IDs.

### `search_emails`

- **Description**: Search Gmail messages using IMAP search criteria.
- **Parameters**:
  - `mailbox`: The Gmail label to search within (e.g., "INBOX").
  - `criteria`: IMAP search criteria (e.g., "ALL").
  - `limit`: Maximum number of messages to return.
- **Returns**: A list of matching Gmail messages.

### `analyze_inbox`

- **Description**: Analyze email patterns and provide insights from your Gmail inbox.
- **Parameters**:
  - `days`: Number of days to analyze (default: 7).
- **Returns**: Insights into email activity, sender patterns, and more.

### `migrate_email_to_gcs`

- **Description**: Migrate a Gmail message to Google Cloud Storage.
- **Parameters**:
  - `uid`: Unique identifier of the Gmail message.
  - `folder`: Gmail label containing the message.
  - `gcs_prefix`: GCS folder to store the email in.
- **Returns**: Paths to the stored email data and attachments.

For a full list of tools and their parameters, refer to the source code or use the `help` command in the server.
