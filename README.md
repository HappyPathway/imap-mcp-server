# Gmail MCP Server

The `imap-mcp-server` is now specifically designed for Gmail, providing AI-powered analysis and management capabilities for Gmail accounts. It leverages the Gmail API for seamless integration and advanced features.

## Features

- **Gmail-Specific Integration**: Built exclusively for Gmail accounts using the Gmail API.
- **AI-Powered Analysis**: Analyze email patterns, prioritize messages, and gain insights into your Gmail inbox.
- **Smart Folder Management**: Create and manage smart folders with custom filtering rules for Gmail.
- **Google Cloud Storage Integration**: Migrate and store Gmail messages and attachments in Google Cloud Storage.
- **Batch Processing**: Perform bulk actions on Gmail messages based on custom criteria.

## MCP Server Configuration

To use this server with VS Code's MCP (Model Context Protocol) functionality, add the following configuration to your VS Code `settings.json`:

```json
"mcp": {
  "inputs": [
    {
      "type": "promptString",
      "id": "gmail-username",
      "description": "Gmail Username"
    },
    {
      "type": "promptString",
      "id": "gmail-password",
      "description": "Gmail Password",
      "password": true
    },
    {
      "type": "promptString",
      "id": "gemini-key",
      "description": "Gemini API Key",
      "password": true
    },
    {
      "type": "promptString",
      "id": "gcs-credentials",
      "description": "Google Cloud Service Account JSON",
      "password": true
    }
  ],
  "servers": {
    "imap-mcp": {
      "type": "stdio",
      "command": "${userHome}/git/imap-mcp-server/venv/bin/python",
      "args": [
        "${userHome}/git/imap-mcp-server/src/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "${input:gemini-key}",
        "IMAP_HOST": "imap.gmail.com",
        "ANALYTICS_BATCH_SIZE": "50",
        "ANALYTICS_CACHE_DURATION": "60",
        "ANALYTICS_THREAD_ANALYSIS": "true",
        "ANALYTICS_PRIORITY_SCORING": "true",
        "GCS_BUCKET": "imap-mcp-server",
        "ANALYTICS_SENDER_THRESHOLD": "7",
        "ANALYTICS_DOMAIN_THRESHOLD": "10",
        "ANALYTICS_UPDATE_INTERVAL": "3600",
        "ANALYTICS_LABEL_TRACKING": "true",
        "ANALYTICS_TYPE_CLASSIFICATION": "true",
        "LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### Configuration Options

- **Environment Variables**:
  - `GEMINI_API_KEY`: Your Gemini API key for AI-powered analysis
  - `IMAP_HOST`: Gmail IMAP server (default: imap.gmail.com)
  - `ANALYTICS_BATCH_SIZE`: Number of emails to process in each batch (default: 50)
  - `ANALYTICS_CACHE_DURATION`: Cache duration in minutes (default: 60)
  - `ANALYTICS_THREAD_ANALYSIS`: Enable thread analysis (default: true)
  - `ANALYTICS_PRIORITY_SCORING`: Enable priority scoring for emails (default: true)
  - `GCS_BUCKET`: Google Cloud Storage bucket name for email storage
  - `ANALYTICS_SENDER_THRESHOLD`: Minimum emails from a sender to trigger analysis (default: 7)
  - `ANALYTICS_DOMAIN_THRESHOLD`: Minimum emails from a domain to trigger analysis (default: 10)
  - `ANALYTICS_UPDATE_INTERVAL`: Analysis update interval in seconds (default: 3600)
  - `ANALYTICS_LABEL_TRACKING`: Enable label tracking (default: true)
  - `ANALYTICS_TYPE_CLASSIFICATION`: Enable email type classification (default: true)
  - `LOG_LEVEL`: Logging level (default: ERROR)

### Prerequisites

Before using the server:

1. Set up a Python virtual environment in the project directory
2. Install the required dependencies using `pip install -r requirements.txt`
3. Configure your VS Code settings as shown above
4. Ensure you have valid credentials for:
   - Gmail account (username and password)
   - Gemini API key
   - Google Cloud Service Account (for GCS integration)

## Requirements

- A Gmail account with API access enabled.
- Google Cloud credentials for accessing Gmail API and Google Cloud Storage.
- Python 3.8 or higher.

## Tools

The `gmail-mcp-server` provides the following tools for managing and analyzing Gmail accounts:

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
