# IMAP MCP Server

A Model Context Protocol (MCP) server that provides email access capabilities through IMAP with AI-powered email analysis. This server allows AI assistants to interact with email accounts using standard IMAP operations and extract structured data using Gemini AI.

## Requirements

### Environment Variables

The following environment variables are required for the server to function:

```bash
# Required for IMAP connection
IMAP_SERVER="imap.gmail.com"  # Your IMAP server address
IMAP_USERNAME="your.email@example.com"
IMAP_PASSWORD="your-app-specific-password"

# Required for AI analysis features
GOOGLE_API_KEY="your-gemini-api-key"
```

### Email Provider Setup

1. For Gmail:
   - Enable 2-factor authentication
   - Generate an App Password for use with this server
   - Use 'imap.gmail.com' as the IMAP server

2. For Outlook:
   - Use 'outlook.office365.com' as the IMAP server
   - Enable 2-factor authentication
   - Generate an App Password

3. For other providers:
   - Check your email provider's IMAP settings
   - Ensure IMAP access is enabled
   - Use appropriate security credentials

## Quick Start

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```bash
IMAP_SERVER="imap.gmail.com"
IMAP_USERNAME="your.email@example.com"
IMAP_PASSWORD="your-app-specific-password"
GOOGLE_API_KEY="your-gemini-api-key"
```

4. Run the server:
```bash
python src/server.py
```

## VS Code Integration

This server is designed to work seamlessly with VS Code using stdio transport. 

### VS Code Configuration

1. Install the VS Code MCP extension from the marketplace.

2. Ensure you have the following files in your `.vscode` directory:

   `mcp.json`:
   ```json
   {
     "servers": {
       "imap-mcp": {
         "type": "stdio",
         "command": "python",
         "args": ["src/server.py"],
         "env": {
           "IMAP_SERVER": "${env:IMAP_SERVER}",
           "IMAP_USERNAME": "${env:IMAP_USERNAME}",
           "IMAP_PASSWORD": "${env:IMAP_PASSWORD}",
           "GOOGLE_API_KEY": "${env:GOOGLE_API_KEY}"
         }
       }
     }
   }
   ```

   `settings.json`:
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
     "python.analysis.extraPaths": ["${workspaceFolder}/src"],
     "python.formatting.provider": "black",
     "editor.formatOnSave": true
   }
   ```

3. Environment Setup:
   - Create a `.env` file in the workspace root with your credentials (see Requirements section)
   - VS Code will automatically load these environment variables when running the server

4. The server will be available to VS Code's MCP extension automatically.

### Using the Server in VS Code

1. Start the Server:
   - Open the Command Palette (Cmd/Ctrl + Shift + P)
   - Type "MCP: Connect to Server"
   - Select "imap-mcp" from the list

2. Verify Connection:
   - Check the VS Code status bar for the MCP connection status
   - The server log output will be visible in the VS Code Output panel

3. Test the Connection:
   - Use the `connect_imap` tool first to establish a connection
   - Try `list_folders` to verify IMAP access is working
   - Test email analysis with a simple schema

## Tools and Features

### Core Email Tools

1. `connect_imap`
   ```python
   connect_imap(host: str, username: str, password: str) -> str
   ```
   Establishes connection to your IMAP server. Must be called first before using other tools.

2. `list_folders`
   ```python
   list_folders() -> List[str]
   ```
   Returns all available mail folders (inbox, sent, drafts, etc.).

3. `list_messages`
   ```python
   list_messages(folder: str, limit: Optional[int] = 10) -> List[Dict]
   ```
   Lists messages in a specified folder with their basic metadata.

4. `read_message`
   ```python
   read_message(folder: str, message_id: str) -> Dict
   ```
   Retrieves full message content including body and attachments.

5. `search_messages`
   ```python
   search_messages(folder: str, criteria: str, limit: Optional[int] = 10) -> List[Dict]
   ```
   Searches messages using IMAP search criteria.

6. `move_messages`
   ```python
   move_messages(source_folder: str, target_folder: str, message_ids: List[str]) -> str
   ```
   Moves messages between folders. This performs a copy + delete operation to ensure message safety.
   
   Example:
   ```python
   # Move unread messages from inbox to archive
   messages = search_messages("INBOX", "UNSEEN", limit=5)  # Get unread messages
   message_ids = [msg["id"] for msg in messages]
   move_messages("INBOX", "Archive", message_ids)
   ```

7. `create_folder`
   ```python
   create_folder(folder_name: str) -> str
   ```
   Creates a new folder in the IMAP mailbox.
   
   Example:
   ```python
   # Create a simple folder
   create_folder("Reports")
   
   # Create a nested folder structure
   create_folder("Projects/Active")
   create_folder("Projects/Archived")
   
   # Create folder and move messages into it
   create_folder("Priority")
   messages = search_messages("INBOX", "FROM boss@company.com", limit=10)
   message_ids = [msg["id"] for msg in messages]
   move_messages("INBOX", "Priority", message_ids)
   ```

8. `mark_flagged`
   ```python
   mark_flagged(folder: str, message_ids: List[str], flag: bool = True) -> str
   ```
   Flag or unflag (star/unstar) messages for follow-up.
   
   Example:
   ```python
   # Flag important messages
   messages = search_messages("INBOX", "FROM boss@company.com UNSEEN")
   mark_flagged("INBOX", [msg["id"] for msg in messages])
   ```

9. `mark_read`
   ```python
   mark_read(folder: str, message_ids: List[str], read: bool = True) -> str
   ```
   Mark messages as read or unread.
   
   Example:
   ```python
   # Mark processed messages as read
   mark_read("INBOX", [msg["id"] for msg in processed_messages])
   ```

### Advanced Email Management

12. `get_thread`
    ```python
    get_thread(folder: str, message_id: str) -> List[Dict]
    ```
    Get all messages in a conversation thread, sorted by date.
    
    Example:
    ```python
    # Find and organize an entire email thread
    thread = get_thread("INBOX", message_id)
    print(f"Thread has {len(thread)} messages")
    ```

13. `organize_thread`
    ```python
    organize_thread(folder: str, message_id: str, target_folder: str) -> str
    ```
    Move an entire email thread to a different folder.
    
    Example:
    ```python
    # Move entire project discussion to project folder
    organize_thread("INBOX", message_id, "Projects/ProjectX")
    ```

14. `analyze_importance`
    ```python
    analyze_importance(folder: str, message_id: str) -> Dict[str, Any]
    ```
    AI-powered analysis of email importance using multiple factors.
    
    Example:
    ```python
    importance = analyze_importance("INBOX", message_id)
    if importance["importance_analysis"]["importance_level"] == "High":
        mark_flagged("INBOX", [message_id])
    ```

15. `find_duplicates`
    ```python
    find_duplicates(folder: str) -> Dict[str, List[str]]
    ```
    Find duplicate messages in a folder by comparing content and headers.
    
    Example:
    ```python
    duplicates = find_duplicates("INBOX")
    for duplicate_set in duplicates.values():
        # Keep newest copy, move others to trash
        newest = duplicate_set[0]
        move_messages("INBOX", "Trash", duplicate_set[1:])
    ```

16. `suggest_cleanup`
    ```python
    suggest_cleanup(folder: str) -> Dict[str, List[Dict]]
    ```
    AI-powered analysis for inbox cleanup, identifying old, duplicate, or low-priority messages.
    
    Example:
    ```python
    cleanup = suggest_cleanup("INBOX")
    # Move old newsletters to archive
    move_messages("INBOX", "Archive", cleanup["cleanup_suggestions"]["newsletter_messages"])
    # Delete duplicate messages
    for dupes in cleanup["duplicates"].values():
        move_messages("INBOX", "Trash", dupes[1:])  # Keep one copy
    ```

17. `analyze_and_label`
    ```python
    analyze_and_label(folder: str, message_ids: List[str]) -> Dict[str, List[str]]
    ```
    AI-powered analysis to suggest labels and categorization for messages.
    
    Example:
    ```python
    # Get unread messages
    messages = search_messages("INBOX", "UNSEEN")
    # Analyze and organize them
    labels = analyze_and_label("INBOX", [msg["id"] for msg in messages])
    
    # Create folders for projects and move messages
    for msg_id, project in labels["project_tags"].items():
        folder_name = f"Projects/{project}"
        create_folder(folder_name)
        move_messages("INBOX", folder_name, [msg_id])
    
    # Flag high-priority items
    for msg_id, priority in labels["priority_levels"].items():
        if priority == "High":
            mark_flagged("INBOX", [msg_id])
    ```

### Example: Complete Inbox Organization

Here's a comprehensive example that uses multiple tools to organize an inbox:

```python
# 1. Initial Analysis
cleanup = await suggest_cleanup("INBOX")
labels = await analyze_and_label("INBOX", [msg["id"] for msg in await list_messages("INBOX")])

# 2. Handle Duplicates
for duplicate_set in cleanup["duplicates"].values():
    await move_messages("INBOX", "Trash", duplicate_set[1:])

# 3. Create Project Structure
for project in set(labels["project_tags"].values()):
    await create_folder(f"Projects/{project}")

# 4. Organize by Priority
high_priority = [
    msg_id for msg_id, priority in labels["priority_levels"].items()
    if priority == "High"
]
await create_folder("Priority")
await move_messages("INBOX", "Priority", high_priority)
await mark_flagged("Priority", high_priority)

# 5. Move Low-Priority Items
await create_folder("Low Priority")
await move_messages(
    "INBOX", 
    "Low Priority",
    cleanup["cleanup_suggestions"]["low_priority"]
)

# 6. Archive Old Items
await create_folder("Archive")
await move_messages(
    "INBOX",
    "Archive",
    cleanup["cleanup_suggestions"]["old_messages"]
)

# 7. Organize by Project
for msg_id, project in labels["project_tags"].items():
    await organize_thread("INBOX", msg_id, f"Projects/{project}")

# 8. Mark Processed Items as Read
all_folders = await list_folders()
for folder in all_folders:
    messages = await list_messages(folder)
    await mark_read(folder, [msg["id"] for msg in messages])
```

### AI-Powered Analysis

The `analyze_email` tool uses Gemini AI to extract structured data from emails:
```python
analyze_email(folder: str, message_id: str, data_schema: Dict[str, str]) -> Dict[str, Any]
```

#### Example Usage

1. Meeting Information Extraction:
   ```python
   schema = {
       "meeting_time": "When the meeting is scheduled for",
       "location": "Where the meeting will be held",
       "attendees": "List of meeting attendees",
       "agenda_items": "List of agenda items to be discussed"
   }
   ```

2. Task Extraction:
   ```python
   schema = {
       "action_items": "List of tasks or action items assigned",
       "due_dates": "Any mentioned deadlines or due dates",
       "assignees": "People assigned to tasks",
       "priority_level": "Priority level of tasks if mentioned"
   }
   ```

3. Travel Itinerary:
   ```python
   schema = {
       "flight_details": "Flight numbers and times",
       "hotel_info": "Hotel booking details",
       "check_in": "Check-in date and time",
       "check_out": "Check-out date and time",
       "reservation_numbers": "Any reservation or booking numbers"
   }
   ```

### IMAP Search Examples

The `search_messages` tool supports standard IMAP search criteria:

1. Date-based search:
   ```python
   "SINCE 1-Jan-2024 BEFORE 1-Feb-2024"
   ```

2. Sender/recipient search:
   ```python
   "FROM john@example.com"
   "TO support@company.com"
   ```

3. Content search:
   ```python
   "SUBJECT meeting"
   "BODY project status"
   ```

4. Status-based search:
   ```python
   "UNSEEN"  # Unread messages
   "FLAGGED"  # Starred/flagged messages
   ```

5. Complex queries:
   ```python
   "FROM john@example.com SINCE 1-Jan-2024 UNSEEN"
   ```

## Error Handling

The server includes comprehensive error handling for:
- IMAP connection issues
- Authentication failures
- Invalid folder names or message IDs
- AI analysis failures
- Search criteria errors

All errors are logged and include descriptive messages to help diagnose issues.

## Security Considerations

1. Credentials:
   - Store credentials in environment variables or .env file
   - Never commit credentials to version control
   - Use app-specific passwords when available

2. API Keys:
   - Keep your Gemini API key secure
   - Monitor API usage and set appropriate limits

3. Email Access:
   - Use read-only access when possible
   - Implement proper session management
   - Always properly close IMAP connections

## Troubleshooting

1. Connection Issues:
   - Verify IMAP server address and port
   - Check credentials and app-specific password
   - Ensure IMAP access is enabled for your account

2. Authentication Errors:
   - Verify username and password
   - Check for 2FA requirements
   - Ensure app-specific password is valid

3. AI Analysis Issues:
   - Verify Gemini API key
   - Check API quota and limits
   - Validate schema format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[MIT License](LICENSE)
