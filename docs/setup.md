# Setup Guide for Gmail MCP Server

This guide walks you through setting up the `imap-mcp-server` for managing and analyzing Gmail accounts.

## Prerequisites

1. **Gmail API Access**:

   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable the Gmail API for your project.
   - Create OAuth 2.0 credentials and download the credentials JSON file.

2. **Google Cloud Storage**:

   - Enable the Cloud Storage API in your Google Cloud project.
   - Create a storage bucket for storing email data.

3. **Environment Variables**:
   - Set the following environment variables:
     - `GEMINI_API_KEY`: Your Gemini API key for AI-powered analysis.
     - `GCP_PROJECT`: Your Google Cloud project ID.
     - `GCS_BUCKET`: The name of your Google Cloud Storage bucket.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/imap-mcp-server.git
   cd imap-mcp-server
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Place your Gmail API credentials file in the path specified in the configuration (`~/.imap-mcp/credentials.json` by default).

## Running the Server

Start the server with:

```bash
python src/server.py
```

The server will connect to your Gmail account and provide tools for managing and analyzing your inbox.
