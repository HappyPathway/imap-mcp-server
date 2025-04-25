"""Email analytics module using Gemini code execution for intelligent analysis."""

from typing import List, Dict, Optional
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel
import logging

from database import get_session
from models import AnalyticsCache

logger = logging.getLogger(__name__)

class EmailMetadata(BaseModel):
    """Structure for storing email metadata for analysis"""
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: datetime
    thread_id: Optional[str] = None
    references: List[str] = None
    content_preview: str = ""
    importance_score: float = 0.0
    labels: List[str] = None
    category: Optional[str] = None
    response_time: Optional[float] = None  # in minutes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for analysis"""
        data = self.dict()
        data['date'] = self.date.isoformat()
        return data

class EmailAnalytics:
    """Core class for email analytics using Gemini code execution"""
    
    def __init__(self):
        """Initialize the analytics engine"""
        self.model = genai.GenerativeModel('gemini-1.0-pro')
        self._cache = {}

    async def analyze_patterns(self, messages: List[EmailMetadata], enable_thread_analysis: bool) -> Dict:
        """Analyze patterns in a set of email messages"""
        # Convert messages to a format suitable for analysis
        email_data = [msg.to_dict() for msg in messages]
        
        prompt = f"""Analyze this email dataset to identify key patterns and insights.
        Focus on:
        1. Communication patterns
        2. Topic clustering
        3. Response times
        4. Priority patterns
        
        Dataset: {json.dumps(email_data, indent=2)}
        
        Generate Python code that:
        1. Processes this data structure
        2. Calculates relevant statistics
        3. Returns insights as a structured dictionary
        
        The code should handle:
        - Sender/recipient patterns
        - Subject clustering
        - Time-based patterns
        - Thread relationships (if thread_id exists)
        """
        
        response = await self.model.generate_content(prompt)
        
        try:
            # Execute the generated analysis code
            analysis_code = response.text.split("```python")[1].split("```")[0]
            local_vars = {'email_data': email_data}
            exec(analysis_code, {}, local_vars)
            return local_vars.get('results', {})
        except Exception as e:
            logger.error(f"Error executing analysis code: {str(e)}")
            return {"error": str(e)}

    async def suggest_folders(self, messages: List[EmailMetadata], enable_priority: bool) -> List[Dict]:
        """Generate intelligent folder suggestions based on message patterns"""
        email_data = [msg.to_dict() for msg in messages]
        
        prompt = f"""Based on this email dataset, suggest intelligent folder organization rules.
        Consider:
        1. Content patterns
        2. Sender/recipient groupings
        3. Topic relationships
        4. Priority levels (if priority scoring is enabled: {enable_priority})
        
        Dataset: {json.dumps(email_data, indent=2)}
        
        Generate Python code that:
        1. Analyzes the email patterns
        2. Creates folder suggestions with rules
        3. Returns a list of folder configurations
        
        Each folder should have:
        - name: Folder name
        - description: Purpose of the folder
        - rules: List of criteria for messages
        - priority: Importance level (if enabled)
        """
        
        response = await self.model.generate_content(prompt)
        
        try:
            analysis_code = response.text.split("```python")[1].split("```")[0]
            local_vars = {'email_data': email_data, 'enable_priority': enable_priority}
            exec(analysis_code, {}, local_vars)
            return local_vars.get('folder_suggestions', [])
        except Exception as e:
            logger.error(f"Error generating folder suggestions: {str(e)}")
            return []

    async def calculate_importance(self, message: EmailMetadata) -> float:
        """Calculate importance score for an email"""
        cache_key = f"importance_{message.message_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        prompt = f"""Calculate an importance score (0.0-1.0) for this email:
        
        Subject: {message.subject}
        From: {message.sender}
        To: {', '.join(message.recipients)}
        Preview: {message.content_preview}
        Thread ID: {message.thread_id}
        
        Consider:
        1. Sender importance (e.g., manager, team member)
        2. Subject urgency indicators
        3. Content priority signals
        4. Thread context
        5. Response patterns
        
        Generate Python code that:
        1. Analyzes these factors
        2. Weights them appropriately
        3. Returns a final score between 0.0 and 1.0
        """
        
        response = await self.model.generate_content(prompt)
        
        try:
            scoring_code = response.text.split("```python")[1].split("```")[0]
            local_vars = {'message': message.to_dict()}
            exec(scoring_code, {}, local_vars)
            score = min(max(float(local_vars.get('score', 0.0)), 0.0), 1.0)
            self._cache[cache_key] = score
            return score
        except Exception as e:
            logger.error(f"Error calculating importance score: {str(e)}")
            return 0.0
            
    def clear_cache(self) -> None:
        """Clear the analytics cache"""
        self._cache.clear()
