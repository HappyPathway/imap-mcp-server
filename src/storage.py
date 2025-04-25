"""Storage manager for IMAP MCP Server with GCS synchronization."""

import os
import json
import time
import socket
from datetime import datetime
from pathlib import Path
from google.cloud import storage
import logging

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages interaction with Google Cloud Storage."""
    
    def __init__(self):
        self.client = storage.Client()
        self.db_blob_name = 'imap_mcp.db'
        self.local_db_path = Path(__file__).parent / 'imap_mcp.db'
        self.config_path = Path(__file__).parent / 'config' / 'gcs.json'
        self.bucket_name = self._get_bucket_name()
        self.bucket = self.client.bucket(self.bucket_name)
        self.db_lock_blob_name = 'imap_mcp.db.lock'
        self.lock_retry_attempts = 50
        self.lock_retry_delay = 0.5  # seconds

    def _get_bucket_name(self) -> str:
        """Get bucket name from config or environment"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
                if 'GCS_BUCKET_NAME' in config:
                    return config['GCS_BUCKET_NAME']
        
        # Fallback to environment variable
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        if bucket_name:
            return bucket_name
            
        raise ValueError("No GCS bucket configured. Set GCS_BUCKET_NAME in config/gcs.json or environment.")

    def _ensure_local_dir(self, path: Path) -> None:
        """Ensure local directory exists"""
        path.parent.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self) -> bool:
        """Try to acquire the database lock"""
        lock_content = {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }

        for attempt in range(self.lock_retry_attempts):
            try:
                blob = self.bucket.blob(self.db_lock_blob_name)
                if not blob.exists():
                    # Try to create the lock file
                    blob.upload_from_string(json.dumps(lock_content))
                    logger.info("Database lock acquired")
                    return True
                else:
                    # Lock exists, check if it's stale (older than 5 minutes)
                    try:
                        lock_data = json.loads(blob.download_as_string())
                        lock_time = datetime.fromisoformat(lock_data['timestamp'])
                        if (datetime.now() - lock_time).total_seconds() > 300:
                            logger.warning("Found stale lock, removing it")
                            self.release_lock()
                            continue
                    except:
                        # If we can't read the lock file, assume it's corrupt
                        self.release_lock()
                        continue

                logger.debug(f"Lock exists, waiting... (attempt {attempt + 1}/{self.lock_retry_attempts})")
                time.sleep(self.lock_retry_delay)
            except Exception as e:
                logger.error(f"Error acquiring lock: {str(e)}")
                return False

        logger.error("Failed to acquire lock after maximum attempts")
        return False

    def release_lock(self) -> bool:
        """Release the database lock"""
        try:
            blob = self.bucket.blob(self.db_lock_blob_name)
            if blob.exists():
                blob.delete()
                logger.info("Database lock released")
            return True
        except Exception as e:
            logger.error(f"Error releasing lock: {str(e)}")
            return False

    def force_unlock(self) -> bool:
        """Force remove the database lock regardless of state"""
        try:
            blob = self.bucket.blob(self.db_lock_blob_name)
            if blob.exists():
                blob.delete()
                logger.info("Database lock forcefully removed")
            return True
        except Exception as e:
            logger.error(f"Error force removing lock: {str(e)}")
            return False

    def download_db(self) -> bool:
        """Download the database file from GCS"""
        try:
            blob = self.bucket.blob(self.db_blob_name)
            if not blob.exists():
                logger.info("No existing database in GCS")
                # Create empty database file if it doesn't exist locally
                if not self.local_db_path.exists():
                    self.local_db_path.touch()
                return False
                
            logger.info("Downloading database from GCS")
            self._ensure_local_dir(self.local_db_path)
            blob.download_to_filename(self.local_db_path)
            return True
        except Exception as e:
            logger.error(f"Error downloading database: {str(e)}")
            # Create empty database file on error
            if not self.local_db_path.exists():
                self.local_db_path.touch()
            return False

    def upload_db(self) -> bool:
        """Upload the database file to GCS"""
        try:
            if not self.local_db_path.exists():
                logger.error("No local database file to upload")
                return False
                
            logger.info("Uploading database to GCS")
            blob = self.bucket.blob(self.db_blob_name)
            blob.upload_from_filename(self.local_db_path)
            return True
        except Exception as e:
            logger.error(f"Error uploading database: {str(e)}")
            return False

    def sync_db(self) -> bool:
        """Download database from GCS without lock management"""
        return self.download_db()

    def sync_and_upload_db(self) -> bool:
        """Sync local DB with GCS and upload changes"""
        if not self.acquire_lock():
            raise Exception("Could not acquire database lock")
        try:
            self.sync_db()
            if self.local_db_path.exists():
                logger.info("Uploading database to GCS")
                blob = self.bucket.blob(self.db_blob_name)
                blob.upload_from_filename(self.local_db_path)
                return True
            return False
        finally:
            self.release_lock()
