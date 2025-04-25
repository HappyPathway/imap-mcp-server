# filepath: /Users/darnold/git/imap-mcp-server/src/config.py
"""Configuration and initialization for IMAP MCP Server."""

import logging
from pathlib import Path
import google.generativeai as genai
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IMAPConfig(BaseModel):
    host: str
    username: str
    password: str

class GeminiConfig(BaseModel):
    apiKey: str

class AnalyticsConfig(BaseModel):
    batchSize: int = 50
    cacheDuration: int = 60
    enableThreadAnalysis: bool = True
    enablePriorityScoring: bool = True

# Ensure config directory exists
config_dir = Path(__file__).parent / 'config'
config_dir.mkdir(exist_ok=True)
