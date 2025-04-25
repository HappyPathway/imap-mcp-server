import imaplib
import os
import ssl
import email
import logging
import asyncio
from email.header import decode_header
from typing import Optional, List, Dict, Tuple
try:
    import aioimaplib
except ImportError:
    print("aioimaplib not installed, using standard imaplib")
    aioimaplib = None

from .google_auth import GoogleAuth

class EmailService:
    def __init__(self):
        self.host = os.getenv('IMAP_HOST', 'imap.gmail.com')
        self.auth = GoogleAuth()
        self.imap = None
        self.use_async = aioimaplib is not None
        self.connected = False
        self._create_ssl_context()
        self._setup_logging()

    def _create_ssl_context(self):
        # Create secure SSL context for Gmail
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        # Gmail requires modern TLS
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    def _setup_logging(self):
        self.logger = logging.getLogger(__name__)
        # Set to DEBUG level for more verbose output
        self.logger.setLevel(logging.DEBUG)
        # Add a stream handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def connect(self) -> bool:
        """Connect to IMAP server using OAuth2 authentication."""
        try:
            if self.connected:
                self.logger.debug("Already connected to IMAP server")
                return True
                
            auth_string = self.auth.get_imap_auth_string()
            
            if self.use_async:
                self.imap = aioimaplib.IMAP4_SSL(
                    host=self.host,
                    ssl_context=self.ssl_context
                )
                await self.imap.wait_hello_from_server()
                
                # Gmail's XOAUTH2 expects the auth string directly
                response = await self.imap.send_command(
                    f'AUTHENTICATE XOAUTH2 {auth_string}'
                )
                if response.result == 'OK':
                    self.connected = True
                    self.logger.info("Successfully connected to IMAP server using OAuth2")
                    return True
                else:
                    raise RuntimeError(f"Authentication failed: {response.result}")
            else:
                raise RuntimeError("Async IMAP library required for OAuth2 authentication")

            # Get fresh OAuth2 authentication string
            try:
                auth_string = self.auth.get_imap_auth_string()
            except FileNotFoundError as e:
                self.logger.error("OAuth2 credentials not found. Please set up credentials.json")
                raise RuntimeError("OAuth2 credentials not found. Run setup process first.") from e
            except Exception as e:
                self.logger.error(f"OAuth2 authentication failed: {e}")
                raise RuntimeError("Failed to get OAuth2 token. Try removing ~/.imap-mcp/token.pickle") from e

            if self.use_async:
                self.imap = aioimaplib.IMAP4_SSL(
                    host=self.host,
                    ssl_context=self.ssl_context
                )
                await self.imap.wait_hello_from_server()
                
                # Use XOAUTH2 authentication
                response = await self.imap.authenticate('XOAUTH2', lambda x: auth_string)
                if response.result != 'OK':
                    raise RuntimeError(f"IMAP authentication failed: {response.result}")
                
                self.connected = True
                self.logger.info("Successfully connected to IMAP server using OAuth2")
                return True
            else:
                raise RuntimeError("Async IMAP library required for OAuth2 authentication")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to IMAP server: {str(e)}")
            self.connected = False
            
            if "Invalid credentials" in str(e):
                # Token might be expired or revoked
                try:
                    os.remove(self.auth.config.token_path)
                    self.logger.info("Removed expired token. Please try connecting again.")
                except OSError:
                    pass
                    
            raise

    async def get_folders(self) -> List[Dict[str, str]]:
        """Get list of all Gmail folders/labels with their attributes"""
        if not self.connected:
            if not await self.connect():
                raise RuntimeError("Could not connect to IMAP server")

        try:
            self.logger.debug("Listing Gmail folders")
            if self.use_async:
                typ, folder_data = await self.imap.list('""', '*')
            else:
                typ, folder_data = self.imap.list('""', '*')

            if typ != 'OK':
                raise RuntimeError(f"Failed to list folders: {typ}")

            folders = []
            for folder_line in folder_data:
                if isinstance(folder_line, bytes):
                    folder_line = folder_line.decode()
                
                # Parse the IMAP list response format
                try:
                    # Handle complex folder names that might contain spaces
                    parts = folder_line.split('" "')
                    if len(parts) >= 2:
                        flags = parts[0].split('(')[1].split(')')[0]
                        name = parts[-1].strip('"')
                        
                        folder_info = {
                            'name': name,
                            'flags': flags.split(),
                            'type': 'System' if name.startswith('[Gmail]') else 'Custom'
                        }
                        folders.append(folder_info)
                except Exception as parse_error:
                    self.logger.warning(f"Could not parse folder line: {folder_line}, error: {parse_error}")
                    continue

            self.logger.info(f"Found {len(folders)} folders")
            return folders

        except Exception as e:
            self.logger.error(f"Error listing folders: {e}")
            raise
    
    async def get_messages(self, folder: str = 'INBOX', limit: int = 10) -> List[Dict[str, str]]:
        """Get messages from a folder using UIDs for stable message identification"""
        if not self.connected:
            if not await self.connect():
                raise RuntimeError("Failed to connect to IMAP server")
            
        messages = []
        try:
            # Select the mailbox/folder
            if self.use_async:
                select_response = await self.imap.select(folder)
                if select_response[0] != 'OK':
                    self.logger.error(f"Failed to select folder {folder}: {select_response}")
                    return []
                
                # Search for all messages and get UIDs
                search_response, data = await self.imap.uid('search', None, 'ALL')
                if search_response != 'OK':
                    self.logger.error(f"Search failed on folder {folder}: {search_response}")
                    return []
            else:
                select_response = self.imap.select(folder)
                if select_response[0] != 'OK':
                    self.logger.error(f"Failed to select folder {folder}: {select_response}")
                    return []
                
                search_response, data = self.imap.uid('search', None, 'ALL')
                if search_response != 'OK':
                    self.logger.error(f"Search failed on folder {folder}: {search_response}")
                    return []

            if not data or not data[0]:
                self.logger.info(f"No messages found in folder {folder}")
                return []

            message_uids = data[0].split() if isinstance(data[0], bytes) else data[0]
            self.logger.debug(f"Found {len(message_uids)} messages in folder {folder}")
            
            if not message_uids:
                return []
                
            # Get most recent messages first (up to limit)
            target_uids = list(reversed(message_uids[-limit:]))
            self.logger.debug(f"Processing {len(target_uids)} most recent messages")
            
            for uid in target_uids:
                try:
                    if self.use_async:
                        fetch_response, msg_data = await self.imap.uid('fetch', uid, '(RFC822)')
                        if fetch_response != 'OK':
                            self.logger.warning(f"Failed to fetch message {uid}: {fetch_response}")
                            continue
                    else:
                        fetch_response, msg_data = self.imap.uid('fetch', uid, '(RFC822)')
                        if fetch_response != 'OK':
                            self.logger.warning(f"Failed to fetch message {uid}: {fetch_response}")
                            continue
                        
                    if not msg_data or not msg_data[0]:
                        self.logger.warning(f"Empty response for message {uid}")
                        continue
                        
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract message details with better error handling
                    subject = ""
                    from_addr = ""
                    date = ""
                    
                    # Safe subject extraction
                    try:
                        if email_message["subject"]:
                            subject_decoded = decode_header(email_message["subject"])[0]
                            subject = subject_decoded[0].decode() if isinstance(subject_decoded[0], bytes) else str(subject_decoded[0])
                    except Exception as subject_error:
                        self.logger.warning(f"Error decoding subject for message {uid}: {subject_error}")
                        subject = "(Subject decode error)"
                    
                    # Safe from address extraction
                    try:
                        if email_message["from"]:
                            from_decoded = decode_header(email_message["from"])[0]
                            from_addr = from_decoded[0].decode() if isinstance(from_decoded[0], bytes) else str(from_decoded[0])
                    except Exception as from_error:
                        self.logger.warning(f"Error decoding from address for message {uid}: {from_error}")
                        from_addr = "(From address decode error)"
                    
                    # Safe date extraction
                    date = email_message["date"] or ""
                    
                    messages.append({
                        "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                        "subject": subject,
                        "from": from_addr,
                        "date": date,
                        "folder": folder
                    })
                except asyncio.CancelledError:
                    # Re-raise cancellation to allow proper async cleanup
                    raise
                except Exception as e:
                    self.logger.error(f"Error processing message {uid}: {e}")
                    continue
                    
            return messages
            
        except asyncio.CancelledError:
            # Re-raise cancellation to allow proper async cleanup
            raise
        except Exception as e:
            self.logger.error(f"Error fetching messages from {folder}: {e}")
            # Check if connection was lost and attempt to reconnect
            if "socket" in str(e).lower() or "connection" in str(e).lower():
                self.logger.info("Connection may have been lost, attempting to reconnect...")
                self.connected = False
                if await self.connect():
                    self.logger.info("Reconnected successfully, retrying operation")
                    return await self.get_messages(folder, limit)
            raise

    async def move_message(self, uid: str, from_folder: str, to_folder: str) -> bool:
        """Move a message between folders using UIDs"""
        if not self.connected:
            if not await self.connect():
                raise RuntimeError("Failed to connect to IMAP server")
            
        try:
            # Select source folder
            if self.use_async:
                select_response = await self.imap.select(from_folder)
                if select_response[0] != 'OK':
                    self.logger.error(f"Failed to select source folder {from_folder}: {select_response}")
                    return False
                
                # Copy message to destination
                copy_response = await self.imap.uid('copy', uid, to_folder)
                if copy_response[0] != 'OK':
                    self.logger.error(f"Failed to copy message {uid} to {to_folder}: {copy_response}")
                    return False
                
                # Mark original for deletion
                store_response = await self.imap.uid('store', uid, '+FLAGS', '(\\Deleted)')
                if store_response[0] != 'OK':
                    self.logger.error(f"Failed to mark message {uid} as deleted: {store_response}")
                    # Message was copied but not deleted - partial success
                    self.logger.warning(f"Message {uid} was copied to {to_folder} but not deleted from {from_folder}")
                    return True
                
                # Expunge to remove deleted messages
                expunge_response = await self.imap.expunge()
                if expunge_response[0] != 'OK':
                    self.logger.warning(f"Expunge command failed: {expunge_response}")
                    # Not critical as message is still marked for deletion
                
            else:
                select_response = self.imap.select(from_folder)
                if select_response[0] != 'OK':
                    self.logger.error(f"Failed to select source folder {from_folder}: {select_response}")
                    return False
                
                copy_response = self.imap.uid('copy', uid, to_folder)
                if copy_response[0] != 'OK':
                    self.logger.error(f"Failed to copy message {uid} to {to_folder}: {copy_response}")
                    return False
                
                store_response = self.imap.uid('store', uid, '+FLAGS', '(\\Deleted)')
                if store_response[0] != 'OK':
                    self.logger.error(f"Failed to mark message {uid} as deleted: {store_response}")
                    # Message was copied but not deleted - partial success
                    self.logger.warning(f"Message {uid} was copied to {to_folder} but not deleted from {from_folder}")
                    return True
                
                expunge_response = self.imap.expunge()
                if expunge_response[0] != 'OK':
                    self.logger.warning(f"Expunge command failed: {expunge_response}")
                    # Not critical as message is still marked for deletion
            
            self.logger.info(f"Successfully moved message {uid} from {from_folder} to {to_folder}")
            return True
            
        except asyncio.CancelledError:
            # Re-raise cancellation to allow proper async cleanup
            raise
        except Exception as e:
            self.logger.error(f"Error moving message {uid}: {e}")
            
            # Check if connection was lost and attempt to reconnect
            if "socket" in str(e).lower() or "connection" in str(e).lower() or "BYE" in str(e):
                self.logger.info("Connection may have been lost, attempting to reconnect...")
                self.connected = False
                if await self.connect():
                    self.logger.info("Reconnected successfully, retrying operation")
                    return await self.move_message(uid, from_folder, to_folder)
                    
            return False

    def get_message_content(self, folder: str, message_id: str) -> Dict:
        """Get full content of a specific message"""
        if not self.imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self.imap.select(folder)
            _, msg_data = self.imap.fetch(message_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                raise RuntimeError(f"Message {message_id} not found in folder {folder}")
                
            return self._parse_message_full(msg_data[0][1])
        except Exception as e:
            self.logger.error(f"Error getting message content: {e}")
            raise

    async def get_message_by_uid(self, folder: str, uid: str) -> Optional[Dict]:
        """Get full content of a specific message by UID"""
        if not self.connected:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            if self.use_async:
                await self.imap.select(folder)
                _, msg_data = await self.imap.uid('fetch', uid, '(RFC822)')
            else:
                self.imap.select(folder)
                _, msg_data = self.imap.uid('fetch', uid, '(RFC822)')
                
            if not msg_data or not msg_data[0]:
                self.logger.warning(f"Message {uid} not found in folder {folder}")
                return None
                
            return self._parse_message_full(msg_data[0][1])
        except Exception as e:
            self.logger.error(f"Error getting message content: {e}")
            raise

    def search_messages(self, folder: str, criteria: str, limit: int = 10) -> List[Dict]:
        """Search for messages in a folder using IMAP search criteria"""
        if not self.imap:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            self.imap.select(folder)
            _, message_numbers = self.imap.search(None, criteria)
            messages = []
            
            for num in message_numbers[0].split()[-limit:]:
                _, msg_data = self.imap.fetch(num, "(RFC822.HEADER)")
                message = self._parse_message_headers(msg_data[0][1])
                message["id"] = num.decode()
                messages.append(message)
                
            return messages
        except Exception as e:
            self.logger.error(f"Error searching messages: {e}")
            raise
    
    def _parse_message_headers(self, email_body: bytes) -> Dict:
        message = email.message_from_bytes(email_body)
        subject = self._decode_header(message["subject"])
        from_ = self._decode_header(message["from"])
        
        return {
            "subject": subject,
            "from": from_,
            "date": message["date"]
        }
        
    def _parse_message_full(self, email_body: bytes) -> Dict:
        message = email.message_from_bytes(email_body)
        subject = self._decode_header(message["subject"])
        from_ = self._decode_header(message["from"])
        to = self._decode_header(message["to"])
        
        body = ""
        attachments = []
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                    
                filename = part.get_filename()
                if filename:
                    # This is an attachment
                    attachments.append({
                        'filename': filename,
                        'content_type': part.get_content_type(),
                        'data': part.get_payload(decode=True)
                    })
                else:
                    # This is message body content
                    if part.get_content_type() == 'text/plain':
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body += payload.decode(charset)
                        except UnicodeDecodeError:
                            body += payload.decode(charset, 'replace')
        else:
            # Not multipart - the payload is the body
            payload = message.get_payload(decode=True)
            charset = message.get_content_charset() or 'utf-8'
            try:
                body = payload.decode(charset)
            except UnicodeDecodeError:
                body = payload.decode(charset, 'replace')
        
        return {
            "subject": subject,
            "from": from_,
            "to": to,
            "date": message["date"],
            "body": body,
            "attachments": attachments
        }

    def _decode_header(self, header: Optional[str]) -> str:
        if not header:
            return ""
        decoded = decode_header(header)[0][0]
        if isinstance(decoded, bytes):
            return decoded.decode()
        return decoded

    async def disconnect(self) -> bool:
        """Safely disconnect from the IMAP server"""
        if not self.imap:
            self.connected = False
            return True
            
        try:
            # Create a timeout to prevent hanging on disconnect
            disconnect_timeout = 5  # seconds
            
            if self.use_async:
                if self.connected:
                    try:
                        # First try to close the selected mailbox
                        close_task = asyncio.create_task(self.imap.close())
                        await asyncio.wait_for(close_task, timeout=disconnect_timeout)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Timeout waiting for IMAP close operation")
                    except Exception as close_error:
                        self.logger.warning(f"Error during IMAP close: {close_error}")
                    
                    try:
                        # Then try to logout properly
                        logout_task = asyncio.create_task(self.imap.logout())
                        await asyncio.wait_for(logout_task, timeout=disconnect_timeout)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Timeout waiting for IMAP logout operation")
                    except Exception as logout_error:
                        self.logger.warning(f"Error during IMAP logout: {logout_error}")
            else:
                if self.connected:
                    try:
                        # Set socket timeout to prevent hanging
                        if hasattr(self.imap, 'sock') and self.imap.sock:
                            self.imap.sock.settimeout(disconnect_timeout)
                        self.imap.close()
                    except Exception as close_error:
                        self.logger.warning(f"Error during IMAP close: {close_error}")
                    
                    try:
                        self.imap.logout()
                    except Exception as logout_error:
                        self.logger.warning(f"Error during IMAP logout: {logout_error}")
            
            self.logger.info("Disconnected from IMAP server")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
        finally:
            # Always mark as disconnected regardless of errors
            self.connected = False
            self.imap = None
            return True

    async def get_gmail_folders(self) -> List[str]:
        """Get Gmail-specific folders"""
        if not self.connected:
            raise RuntimeError("Not connected to IMAP server")

        try:
            if self.use_async:
                _, folder_data = await self.imap.list()
            else:
                _, folder_data = self.imap.list()

            gmail_folders = []
            for folder_line in folder_data:
                folder_name = folder_line.decode().split('"/" ')[-1].strip('"')
                # Include both Gmail system folders and user-created ones
                if folder_name.startswith('[Gmail]') or not folder_name.startswith('['):
                    gmail_folders.append(folder_name)
            
            return gmail_folders
        except Exception as e:
            self.logger.error(f"Error listing Gmail folders: {e}")
            raise

    async def cleanup(self):
        """Safely cleanup resources and close connection"""
        try:
            if self.connected:
                if self.use_async:
                    # Ensure we close any selected mailbox
                    await self.imap.close()
                    # Properly logout
                    await self.imap.logout()
                else:
                    self.imap.close()
                    self.imap.logout()
            self.connected = False
            self.imap = None
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise
        finally:
            # Ensure we mark as disconnected even if cleanup fails
            self.connected = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def get_messages_in_batches(self, folder: str = 'INBOX', batch_size: int = 100, start_date: str = None, end_date: str = None) -> List[Dict[str, str]]:
        """Get messages in batches with date filtering support for older emails"""
        if not self.connected:
            raise RuntimeError("Not connected to IMAP server")
            
        try:
            if self.use_async:
                await self.imap.select(folder)
            else:
                self.imap.select(folder)

            # Build search criteria
            search_criteria = []
            if start_date:
                search_criteria.extend(['SINCE', start_date])
            if end_date:
                search_criteria.extend(['BEFORE', end_date])
            if not search_criteria:
                search_criteria = ['ALL']

            # Get all matching message UIDs
            if self.use_async:
                _, data = await self.imap.uid('search', None, *search_criteria)
            else:
                _, data = self.imap.uid('search', None, *search_criteria)

            message_uids = data[0].split() if isinstance(data[0], bytes) else data[0]
            self.logger.info(f"Found {len(message_uids)} messages matching criteria")

            # Process in batches
            messages = []
            for i in range(0, len(message_uids), batch_size):
                batch_uids = message_uids[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}, size: {len(batch_uids)}")
                
                for uid in batch_uids:
                    try:
                        if self.use_async:
                            _, msg_data = await self.imap.uid('fetch', uid, '(RFC822 FLAGS)')
                        else:
                            _, msg_data = self.imap.uid('fetch', uid, '(RFC822 FLAGS)')
                            
                        if msg_data and msg_data[0]:
                            email_body = msg_data[0][1]
                            flags = msg_data[1] if len(msg_data) > 1 else None
                            email_message = email.message_from_bytes(email_body)
                            
                            # Extract message details with better handling
                            subject = decode_header(email_message.get("subject", ""))[0]
                            subject = subject[0].decode() if isinstance(subject[0], bytes) else str(subject[0])
                            
                            from_header = decode_header(email_message.get("from", ""))[0]
                            from_addr = from_header[0].decode() if isinstance(from_header[0], bytes) else str(from_header[0])
                            
                            # Get message ID for threading
                            message_id = email_message.get("message-id", "")
                            references = email_message.get("references", "").split()
                            in_reply_to = email_message.get("in-reply-to", "")
                            
                            # Extract date with timezone handling
                            date_str = email_message.get("date", "")
                            try:
                                date_parsed = email.utils.parsedate_to_datetime(date_str)
                            except:
                                date_parsed = None
                            
                            messages.append({
                                "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                                "subject": subject,
                                "from": from_addr,
                                "date": date_parsed.isoformat() if date_parsed else date_str,
                                "folder": folder,
                                "message_id": message_id,
                                "references": references,
                                "in_reply_to": in_reply_to,
                                "flags": str(flags) if flags else "",
                                "size": len(email_body)
                            })
                    except Exception as e:
                        self.logger.error(f"Error processing message {uid}: {e}")
                        continue

            return messages
            
        except Exception as e:
            self.logger.error(f"Error in batch processing from {folder}: {e}")
            raise

    async def analyze_batch(self, messages: List[Dict[str, str]], analytics_service) -> Dict:
        """Analyze a batch of messages using the analytics service"""
        try:
            # Convert messages to EmailMetadata objects
            metadata_list = []
            for msg in messages:
                try:
                    metadata = EmailMetadata(
                        message_id=msg['message_id'],
                        subject=msg['subject'],
                        sender=msg['from'],
                        recipients=[],  # We'll add recipient extraction if needed
                        date=datetime.fromisoformat(msg['date']) if isinstance(msg['date'], str) else msg['date'],
                        thread_id=msg.get('in_reply_to', None),
                        references=msg.get('references', []),
                        content_preview=msg.get('subject', '')  # Using subject as preview for now
                    )
                    metadata_list.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error converting message to metadata: {e}")
                    continue

            return await analytics_service.analyze_patterns(metadata_list, enable_thread_analysis=True)
        except Exception as e:
            self.logger.error(f"Error in batch analysis: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if the email service is currently connected."""
        return self.connected
