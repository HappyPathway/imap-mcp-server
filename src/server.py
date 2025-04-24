from mcp.server.fastmcp import FastMCP
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import logging
import os
import google.generativeai as genai
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("IMAP MCP Server")

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))

class IMAPClient:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self._imap = None

    async def connect(self) -> None:
        """Connect to the IMAP server"""
        try:
            self._imap = imaplib.IMAP4_SSL(self.host)
            self._imap.login(self.username, self.password)
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the IMAP server"""
        if self._imap:
            try:
                self._imap.logout()
            except Exception as e:
                logger.error(f"Error during IMAP logout: {e}")

    def get_folders(self) -> List[str]:
        """Get list of mail folders"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        _, folders = self._imap.list()
        return [folder.decode().split('"/"')[-1].strip('"') for folder in folders]

    def get_messages(self, folder: str, limit: int = 10) -> List[Dict]:
        """Get messages from specified folder"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        self._imap.select(folder)
        _, message_numbers = self._imap.search(None, "ALL")
        messages = []
        
        for num in message_numbers[0].split()[-limit:]:
            _, msg_data = self._imap.fetch(num, "(RFC822)")
            email_body = msg_data[0][1]
            message = email.message_from_bytes(email_body)
            
            subject = decode_header(message["subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
                
            from_ = decode_header(message["from"])[0][0]
            if isinstance(from_, bytes):
                from_ = from_.decode()
                
            messages.append({
                "id": num.decode(),
                "subject": subject,
                "from": from_,
                "date": message["date"]
            })
            
        return messages

    def get_message_content(self, folder: str, message_id: str) -> Dict:
        """Get full content of a specific message"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        self._imap.select(folder)
        _, msg_data = self._imap.fetch(message_id.encode(), "(RFC822)")
        email_body = msg_data[0][1]
        message = email.message_from_bytes(email_body)
        
        content = ""
        attachments = []
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get_content_disposition() == 'attachment':
                    attachments.append({
                        'filename': part.get_filename(),
                        'type': part.get_content_type()
                    })
                elif part.get_content_type() == 'text/plain':
                    content += part.get_payload(decode=True).decode()
        else:
            content = message.get_payload(decode=True).decode()
            
        return {
            "subject": decode_header(message["subject"])[0][0],
            "from": decode_header(message["from"])[0][0],
            "date": message["date"],
            "content": content,
            "attachments": attachments
        }

    def search_messages(self, folder: str, criteria: str, limit: int = 10) -> List[Dict]:
        """Search for messages in a folder using IMAP search criteria"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        self._imap.select(folder)
        _, message_numbers = self._imap.search(None, criteria)
        messages = []
        
        for num in message_numbers[0].split()[-limit:]:
            _, msg_data = self._imap.fetch(num, "(RFC822.HEADER)")
            email_body = msg_data[0][1]
            message = email.message_from_bytes(email_body)
            
            subject = decode_header(message["subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
                
            from_ = decode_header(message["from"])[0][0]
            if isinstance(from_, bytes):
                from_ = from_.decode()
                
            messages.append({
                "id": num.decode(),
                "subject": subject,
                "from": from_,
                "date": message["date"]
            })
            
        return messages
    
    def move_messages(self, source_folder: str, target_folder: str, message_ids: List[str]) -> bool:
        """Move messages from one folder to another"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            # Select the source folder
            self._imap.select(source_folder)
            
            # Copy messages to target folder
            for msg_id in message_ids:
                self._imap.copy(msg_id, target_folder)
            
            # Delete messages from source folder (mark as deleted and expunge)
            for msg_id in message_ids:
                self._imap.store(msg_id, '+FLAGS', '\\Deleted')
            self._imap.expunge()
            
            return True
        except Exception as e:
            logger.error(f"Error moving messages: {str(e)}")
            raise RuntimeError(f"Failed to move messages: {str(e)}")

    def create_folder(self, folder_name: str) -> bool:
        """Create a new IMAP folder"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            # Note: Some IMAP servers might require different folder name formats
            # (e.g., with or without leading separator)
            self._imap.create(folder_name)
            return True
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            raise RuntimeError(f"Failed to create folder: {str(e)}")

    def mark_messages_flag(self, folder: str, message_ids: List[str], flag: bool) -> None:
        """Mark messages as flagged/starred"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self._imap.select(folder)
            flag_str = '\\Flagged' if flag else '\\UnFlagged'
            store_str = '+FLAGS' if flag else '-FLAGS'
            
            for msg_id in message_ids:
                self._imap.store(msg_id, store_str, flag_str)
        except Exception as e:
            logger.error(f"Error flagging messages: {str(e)}")
            raise RuntimeError(f"Failed to flag messages: {str(e)}")

    def mark_messages_read(self, folder: str, message_ids: List[str], read: bool) -> None:
        """Mark messages as read/unread"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self._imap.select(folder)
            flag_str = '\\Seen' if read else '\\Unseen'
            store_str = '+FLAGS' if read else '-FLAGS'
            
            for msg_id in message_ids:
                self._imap.store(msg_id, store_str, flag_str)
        except Exception as e:
            logger.error(f"Error marking messages read/unread: {str(e)}")
            raise RuntimeError(f"Failed to mark messages read/unread: {str(e)}")

    def get_message_thread(self, folder: str, message_id: str) -> List[Dict]:
        """Get all messages in the same thread"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self._imap.select(folder)
            _, msg_data = self._imap.fetch(message_id.encode(), "(RFC822)")
            email_body = msg_data[0][1]
            message = email.message_from_bytes(email_body)
            
            # Get message-id and references/in-reply-to headers
            thread_headers = []
            msg_id = message.get("message-id")
            if msg_id:
                thread_headers.append(msg_id)
            
            references = message.get("references", "").split()
            in_reply_to = message.get("in-reply-to", "").split()
            thread_headers.extend(references)
            thread_headers.extend(in_reply_to)
            
            # Search for related messages
            thread_messages = []
            for header in set(thread_headers):
                if not header:
                    continue
                # Search by Message-ID header
                _, nums = self._imap.search(None, f'HEADER MESSAGE-ID "{header}"')
                # Search by References header
                _, ref_nums = self._imap.search(None, f'HEADER REFERENCES "{header}"')
                # Search by In-Reply-To header
                _, reply_nums = self._imap.search(None, f'HEADER IN-REPLY-TO "{header}"')
                
                all_nums = set(nums[0].split() + ref_nums[0].split() + reply_nums[0].split())
                for num in all_nums:
                    _, msg_data = self._imap.fetch(num, "(RFC822.HEADER)")
                    email_body = msg_data[0][1]
                    thread_msg = email.message_from_bytes(email_body)
                    
                    subject = decode_header(thread_msg["subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    from_ = decode_header(thread_msg["from"])[0][0]
                    if isinstance(from_, bytes):
                        from_ = from_.decode()
                    
                    thread_messages.append({
                        "id": num.decode(),
                        "subject": subject,
                        "from": from_,
                        "date": thread_msg["date"]
                    })
            
            return sorted(thread_messages, key=lambda x: email.utils.parsedate_to_datetime(x["date"]))
        except Exception as e:
            logger.error(f"Error getting message thread: {str(e)}")
            raise RuntimeError(f"Failed to get message thread: {str(e)}")

    def find_duplicates(self, folder: str) -> Dict[str, List[str]]:
        """Find duplicate messages in a folder"""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self._imap.select(folder)
            _, message_numbers = self._imap.search(None, "ALL")
            
            # Track messages by content hash
            messages_by_hash = {}
            
            for num in message_numbers[0].split():
                _, msg_data = self._imap.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                
                # Create hash of relevant message parts
                msg = email.message_from_bytes(email_body)
                hash_parts = [
                    msg.get("subject", ""),
                    msg.get("from", ""),
                    msg.get("date", ""),
                    msg.get_payload()
                ]
                msg_hash = hash("".join(str(p) for p in hash_parts))
                
                if msg_hash in messages_by_hash:
                    messages_by_hash[msg_hash].append(num.decode())
                else:
                    messages_by_hash[msg_hash] = [num.decode()]
            
            # Return only the groups that have duplicates
            return {
                hash_val: msg_ids 
                for hash_val, msg_ids in messages_by_hash.items() 
                if len(msg_ids) > 1
            }
        except Exception as e:
            logger.error(f"Error finding duplicates: {str(e)}")
            raise RuntimeError(f"Failed to find duplicates: {str(e)}")

@mcp.tool()
async def connect_imap(host: str, username: str, password: str) -> str:
    """Connect to an IMAP server.
    
    Args:
        host: IMAP server hostname
        username: IMAP account username
        password: IMAP account password
        
    Returns:
        Success message if connection is established
    """
    try:
        client = IMAPClient(host, username, password)
        await client.connect()
        # Store the client instance in the server state
        mcp._imap_client = client
        return "Successfully connected to IMAP server"
    except Exception as e:
        logger.error(f"Failed to connect to IMAP server: {str(e)}")
        raise RuntimeError(f"Failed to connect to IMAP server: {str(e)}")

@mcp.tool()
async def disconnect_imap() -> str:
    """Disconnect from the IMAP server.
    
    Returns:
        Success message if disconnection is successful
    """
    if hasattr(mcp, "_imap_client") and mcp._imap_client:
        try:
            await mcp._imap_client.disconnect()
            mcp._imap_client = None
            return "Successfully disconnected from IMAP server"
        except Exception as e:
            logger.error(f"Error during IMAP disconnection: {str(e)}")
            raise RuntimeError(f"Error during IMAP disconnection: {str(e)}")
    return "No active IMAP connection"

def check_connection():
    """Check if there is an active IMAP connection"""
    if not hasattr(mcp, "_imap_client") or not mcp._imap_client:
        raise RuntimeError("Not connected to IMAP server. Call connect_imap first.")
    
# Update existing tools to use the check_connection helper
@mcp.tool()
async def list_folders() -> List[str]:
    """List all mail folders in the IMAP account.
    
    Returns:
        List of folder names
    """
    check_connection()
    try:
        return mcp._imap_client.get_folders()
    except Exception as e:
        logger.error(f"Error listing folders: {str(e)}")
        raise RuntimeError(f"Error listing folders: {str(e)}")

@mcp.tool()
async def list_messages(folder: str, limit: Optional[int] = 10) -> List[Dict]:
    """List messages in a specified folder.
    
    Args:
        folder: Name of the folder to list messages from
        limit: Maximum number of messages to return (default: 10)
        
    Returns:
        List of message dictionaries containing id, subject, from, and date
    """
    check_connection()
    try:
        return mcp._imap_client.get_messages(folder, limit)
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise RuntimeError(f"Error listing messages: {str(e)}")

@mcp.tool()
async def read_message(folder: str, message_id: str) -> Dict:
    """Read the full content of a specific email message.
    
    Args:
        folder: Name of the folder containing the message
        message_id: ID of the message to read
        
    Returns:
        Dictionary containing message details including subject, from, date, content, and attachments
    """
    check_connection()
    try:
        return mcp._imap_client.get_message_content(folder, message_id)
    except Exception as e:
        logger.error(f"Error reading message: {str(e)}")
        raise RuntimeError(f"Error reading message: {str(e)}")

@mcp.tool()
async def search_messages(folder: str, criteria: str, limit: Optional[int] = 10) -> List[Dict]:
    """Search for messages in a specified folder using IMAP search criteria.
    
    Args:
        folder: Name of the folder to search in
        criteria: IMAP search criteria (e.g., "FROM example@email.com", "SUBJECT meeting")
        limit: Maximum number of messages to return (default: 10)
        
    Returns:
        List of matching message dictionaries containing id, subject, from, and date
    """
    check_connection()
    try:
        return mcp._imap_client.search_messages(folder, criteria, limit)
    except Exception as e:
        logger.error(f"Error searching messages: {str(e)}")
        raise RuntimeError(f"Error searching messages: {str(e)}")

def extract_structured_data(text: str, data_schema: dict) -> dict:
    """Use Gemini to extract structured data from text based on a schema"""
    model = genai.GenerativeModel('gemini-pro')
    
    # Create a prompt that describes what we want to extract
    schema_description = "\n".join([f"- {key}: {value}" for key, value in data_schema.items()])
    prompt = f"""Extract the following information from the email text as JSON:
{schema_description}

Email text:
{text}

Return only valid JSON without any other text."""

    try:
        response = model.generate_content(prompt)
        # The response should be JSON string
        import json
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error extracting structured data: {str(e)}")
        raise RuntimeError(f"Failed to extract structured data: {str(e)}")

@mcp.tool()
async def analyze_email(folder: str, message_id: str, data_schema: Dict[str, str]) -> Dict[str, Any]:
    """Analyze an email message and extract structured data using Gemini.
    
    Args:
        folder: Name of the folder containing the message
        message_id: ID of the message to analyze
        data_schema: Dictionary describing what data to extract, where keys are field names
                    and values are descriptions of what to extract.
                    Example: {"meeting_time": "When the meeting is scheduled for",
                             "attendees": "List of meeting attendees"}
        
    Returns:
        Dictionary containing the extracted structured data according to the provided schema
    """
    check_connection()
    try:
        # First get the message content
        message_data = mcp._imap_client.get_message_content(folder, message_id)
        # Extract structured data from the content
        structured_data = extract_structured_data(message_data["content"], data_schema)
        return {
            "message_info": {
                "subject": message_data["subject"],
                "from": message_data["from"],
                "date": message_data["date"]
            },
            "extracted_data": structured_data
        }
    except Exception as e:
        logger.error(f"Error analyzing message: {str(e)}")
        raise RuntimeError(f"Error analyzing message: {str(e)}")

@mcp.tool()
async def move_messages(source_folder: str, target_folder: str, message_ids: List[str]) -> str:
    """Move messages from one folder to another.
    
    Args:
        source_folder: Name of the folder containing the messages
        target_folder: Name of the destination folder
        message_ids: List of message IDs to move
        
    Returns:
        Success message if the move operation is completed
    """
    check_connection()
    try:
        mcp._imap_client.move_messages(source_folder, target_folder, message_ids)
        return f"Successfully moved {len(message_ids)} messages from {source_folder} to {target_folder}"
    except Exception as e:
        logger.error(f"Error moving messages: {str(e)}")
        raise RuntimeError(f"Error moving messages: {str(e)}")

@mcp.tool()
async def create_folder(folder_name: str) -> str:
    """Create a new folder in the IMAP mailbox.
    
    Args:
        folder_name: Name of the folder to create
        
    Returns:
        Success message if the folder is created
        
    Note:
        Folder names should be simple ASCII strings without special characters.
        Use '/' for hierarchical folders (e.g., 'Parent/Child')
    """
    check_connection()
    try:
        mcp._imap_client.create_folder(folder_name)
        return f"Successfully created folder: {folder_name}"
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise RuntimeError(f"Error creating folder: {str(e)}")

@mcp.tool()
async def mark_flagged(folder: str, message_ids: List[str], flag: bool = True) -> str:
    """Mark messages as flagged/starred or unflagged.
    
    Args:
        folder: Name of the folder containing the messages
        message_ids: List of message IDs to flag/unflag
        flag: True to flag messages, False to unflag them
        
    Returns:
        Success message indicating how many messages were flagged/unflagged
    """
    check_connection()
    try:
        mcp._imap_client.mark_messages_flag(folder, message_ids, flag)
        action = "flagged" if flag else "unflagged"
        return f"Successfully {action} {len(message_ids)} messages"
    except Exception as e:
        logger.error(f"Error flagging messages: {str(e)}")
        raise RuntimeError(f"Error flagging messages: {str(e)}")

@mcp.tool()
async def mark_read(folder: str, message_ids: List[str], read: bool = True) -> str:
    """Mark messages as read or unread.
    
    Args:
        folder: Name of the folder containing the messages
        message_ids: List of message IDs to mark
        read: True to mark as read, False to mark as unread
        
    Returns:
        Success message indicating how many messages were marked
    """
    check_connection()
    try:
        mcp._imap_client.mark_messages_read(folder, message_ids, read)
        action = "read" if read else "unread"
        return f"Successfully marked {len(message_ids)} messages as {action}"
    except Exception as e:
        logger.error(f"Error marking messages: {str(e)}")
        raise RuntimeError(f"Error marking messages: {str(e)}")

@mcp.tool()
async def suggest_folders(folder: str, limit: Optional[int] = 100) -> Dict[str, List[Dict]]:
    """Analyze messages in a folder and suggest organizational structure.
    
    Args:
        folder: Name of the folder to analyze
        limit: Maximum number of messages to analyze
        
    Returns:
        Dictionary mapping suggested folder names to lists of messages that should go in them
    """
    check_connection()
    try:
        # Get messages to analyze
        messages = await list_messages(folder, limit)
        
        # Create analysis prompt for categorization
        categorization_schema = {
            "suggested_folders": "List of suggested folder names based on email content and patterns",
            "categorized_messages": "Dictionary mapping each suggested folder to a list of message IDs that belong in it",
            "categorization_reason": "Brief explanation of the organizational logic"
        }
        
        # Analyze messages in batches to avoid token limits
        batch_size = 10
        all_results = []
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_content = []
            for msg in batch:
                full_msg = await read_message(folder, msg["id"])
                batch_content.append({
                    "id": msg["id"],
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "content": full_msg["content"][:500]  # Use first 500 chars for analysis
                })
            
            # Get Gemini's suggestions for this batch
            analysis = extract_structured_data(
                str(batch_content),
                categorization_schema
            )
            all_results.append(analysis)
        
        # Merge all batch results
        merged_folders = {}
        for result in all_results:
            for folder_name, msgs in result["categorized_messages"].items():
                if folder_name not in merged_folders:
                    merged_folders[folder_name] = []
                merged_folders[folder_name].extend(msgs)
        
        return {
            "suggested_folders": merged_folders,
            "explanation": "Combined analysis of message patterns and content"
        }
    except Exception as e:
        logger.error(f"Error analyzing folder structure: {str(e)}")
        raise RuntimeError(f"Error analyzing folder structure: {str(e)}")

@mcp.tool()
async def auto_categorize(source_folder: str, limit: Optional[int] = 50) -> Dict[str, List[str]]:
    """Automatically categorize messages into existing folders.
    
    Args:
        source_folder: Name of the folder containing messages to categorize
        limit: Maximum number of messages to analyze
        
    Returns:
        Dictionary mapping existing folder names to lists of message IDs that should be moved there
    """
    check_connection()
    try:
        # Get existing folders and messages
        folders = await list_folders()
        messages = await list_messages(source_folder, limit)
        
        # Create analysis prompt for categorization
        categorization_schema = {
            "message_categories": f"Dictionary mapping message IDs to the most appropriate folder from: {folders}",
            "categorization_logic": "Explanation of how messages were matched to folders"
        }
        
        # Analyze messages in batches
        batch_size = 10
        all_categorizations = {}
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_content = []
            for msg in batch:
                full_msg = await read_message(source_folder, msg["id"])
                batch_content.append({
                    "id": msg["id"],
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "content": full_msg["content"][:500]
                })
            
            # Get Gemini's categorization for this batch
            analysis = extract_structured_data(
                str(batch_content),
                categorization_schema
            )
            
            # Merge results
            for msg_id, folder in analysis["message_categories"].items():
                if folder not in all_categorizations:
                    all_categorizations[folder] = []
                all_categorizations[folder].append(msg_id)
        
        return all_categorizations
    except Exception as e:
        logger.error(f"Error auto-categorizing messages: {str(e)}")
        raise RuntimeError(f"Error auto-categorizing messages: {str(e)}")

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()
