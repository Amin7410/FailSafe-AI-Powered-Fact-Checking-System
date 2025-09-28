"""
Content Ingestion Service

Handles input processing for various content types including text, URLs, and files.
"""

import trafilatura
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting and processing various content types"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FailSafe/1.0 (Fact-Checking Bot)'
        })
    
    def process_input(self, payload) -> str:
        """
        Process input based on type (text or URL)
        
        Args:
            payload: ClaimRequest object with text or url
            
        Returns:
            str: Processed content text
        """
        if payload.url:
            return self._process_url(payload.url)
        elif payload.text:
            return payload.text
        else:
            raise ValueError("Either text or url must be provided")
    
    def _process_url(self, url: str) -> str:
        """
        Extract content from URL
        
        Args:
            url: URL to process
            
        Returns:
            str: Extracted content
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            # Fetch content
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract text content
            content = trafilatura.extract(response.text)
            
            if not content:
                # Fallback to basic text extraction
                content = self._basic_text_extraction(response.text)
            
            if not content or len(content.strip()) < 10:
                raise ValueError("No meaningful content found in URL")
            
            logger.info(f"Successfully extracted {len(content)} characters from {url}")
            return content.strip()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise ValueError(f"Failed to fetch content from URL: {e}")
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise ValueError(f"Error processing URL: {e}")
    
    def _basic_text_extraction(self, html: str) -> str:
        """
        Basic HTML text extraction fallback
        
        Args:
            html: HTML content
            
        Returns:
            str: Extracted text
        """
        import re
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.warning(f"Basic text extraction failed: {e}")
            return ""
    
    def validate_content(self, content: str) -> Dict[str, Any]:
        """
        Validate and analyze content quality
        
        Args:
            content: Content to validate
            
        Returns:
            Dict containing validation results
        """
        result = {
            "is_valid": True,
            "length": len(content),
            "word_count": len(content.split()),
            "issues": []
        }
        
        # Check minimum length
        if result["length"] < 10:
            result["is_valid"] = False
            result["issues"].append("Content too short")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r"click\s+here",
            r"free\s+money",
            r"guaranteed\s+profit",
            r"act\s+now",
            r"limited\s+time"
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result["issues"].append(f"Suspicious pattern detected: {pattern}")
        
        return result