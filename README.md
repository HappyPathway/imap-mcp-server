# Gmail MCP Server

The `imap-mcp-server` is now specifically designed for Gmail, providing AI-powered analysis and management capabilities for Gmail accounts. It leverages the Gmail API for seamless integration and advanced features.

## Features

- **Gmail-Specific Integration**: Built exclusively for Gmail accounts using the Gmail API.
- **AI-Powered Analysis**: Analyze email patterns, prioritize messages, and gain insights into your Gmail inbox.
- **Smart Folder Management**: Create and manage smart folders with custom filtering rules for Gmail.
- **Google Cloud Storage Integration**: Migrate and store Gmail messages and attachments in Google Cloud Storage.
- **Batch Processing**: Perform bulk actions on Gmail messages based on custom criteria.

## Requirements

- A Gmail account with API access enabled.
- Google Cloud credentials for accessing Gmail API and Google Cloud Storage.
- Python 3.8 or higher.

## Tools

The `imap-mcp-server` provides the following tools for managing and analyzing Gmail accounts:

### `test_connection`

- **Description**: Tests the Gmail API connection using OAuth2 credentials.
- **Returns**: A list of Gmail labels if the connection is successful.

### `list_labels`

- **Description**: Lists all available labels in your Gmail account.
- **Returns**: A dictionary of label names and IDs.

### `search_emails`

- **Description**: Searches Gmail messages using IMAP search criteria.
- **Parameters**:
  - `mailbox`: The Gmail label to search within (e.g., "INBOX").
  - `criteria`: IMAP search criteria (e.g., "ALL").
  - `limit`: Maximum number of messages to return.
- **Returns**: A list of matching Gmail messages.

### `get_email`

- **Description**: Fetches the complete content of an email by its message ID.
- **Parameters**:
  - `mailbox`: The Gmail label containing the message.
  - `message_id`: The unique identifier of the email.
- **Returns**: The email content and metadata.

### `analyze_inbox`

- **Description**: Analyzes email patterns and provides insights from your Gmail inbox.
- **Parameters**:
  - `days`: Number of days to analyze (default: 7).
- **Returns**: Insights into email activity, sender patterns, and more.

### `get_total_messages`

- **Description**: Retrieves the total number of messages in the inbox.
- **Returns**: The total count of messages.

### `analyze_inbox_state`

- **Description**: Performs a comprehensive analysis of the inbox state.
- **Parameters**:
  - `max_messages`: Maximum number of messages to analyze (default: 100).
- **Returns**: Analysis results, including sender activity, email types, and attachment statistics.

### `move_message`

- **Description**: Moves a message from one folder to another.
- **Parameters**:
  - `uid`: Unique identifier of the email message.
  - `from_folder`: Source folder containing the message.
  - `to_folder`: Destination folder to move the message to.
- **Returns**: Success status of the operation.

### `create_smart_folder`

- **Description**: Creates a smart folder with specified filtering rules.
- **Parameters**:
  - `name`: Name of the smart folder.
  - `rules`: List of filtering rules for the folder.
- **Returns**: Details of the created smart folder.

### `batch_process`

- **Description**: Processes multiple emails in batch based on criteria.
- **Parameters**:
  - `folder`: The folder to process emails from.
  - `action`: Action to perform (e.g., "move", "delete", "label").
  - `filter_criteria`: Criteria to filter emails by.
- **Returns**: Results of the batch operation.

### `migrate_email_to_gcs`

- **Description**: Migrates an email message to Google Cloud Storage.
- **Parameters**:
  - `uid`: Unique identifier of the email message.
  - `folder`: Folder containing the message.
  - `gcs_prefix`: GCS folder to store the email in.
- **Returns**: Paths to the stored email data and attachments.

### `get_folder_summary`

- **Description**: Retrieves summary statistics for a folder.
- **Parameters**:
  - `folder`: The folder to get summary statistics for.
- **Returns**: Summary statistics, including message counts and activity trends.

### `search_messages`

- **Description**: Searches Gmail messages using Gmail's search syntax.
- **Parameters**:
  - `query`: Gmail search query (e.g., "from:someone@example.com has:attachment").
  - `max_results`: Maximum number of messages to return.
- **Returns**: A list of matching Gmail messages.

### `get_thread`

- **Description**: Retrieves all messages in a Gmail thread.
- **Parameters**:
  - `thread_id`: The ID of the thread to retrieve.
- **Returns**: The thread and its messages.

### `get_messages`

- **Description**: Retrieves Gmail messages, optionally filtered by labels.
- **Parameters**:
  - `label_ids`: Optional list of Gmail label IDs to filter by.
  - `max_results`: Maximum number of messages to return.
- **Returns**: A list of Gmail messages.

## Getting Started

1. Set up your Gmail API credentials.
2. Configure the server with your Gmail-specific settings.
3. Run the server to start managing and analyzing your Gmail inbox.

For detailed setup instructions, refer to the [Setup Guide](docs/setup.md).
