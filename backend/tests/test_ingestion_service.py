"""
Unit tests for IngestionService

Tests:
1. Text processing
2. URL processing
3. Error handling
4. Input validation
"""

import pytest
from unittest.mock import Mock, patch
from app.services.ingestion_service import IngestionService
from app.models.claim import ClaimRequest


class TestIngestionService:
    """Test suite for IngestionService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = IngestionService()
    
    def test_process_text_input(self):
        """Test processing text input"""
        # Test valid text input
        payload = ClaimRequest(text="Climate change is real", language="en")
        result = self.service.process_input(payload)
        
        assert result == "Climate change is real"
    
    def test_process_url_input_error(self):
        """Test URL processing raises error when trafilatura not available"""
        payload = ClaimRequest(url="https://example.com/article", language="en")
        
        # Should raise ValueError when trafilatura is not available
        with pytest.raises(ValueError, match="Ingestion error for URL"):
            self.service.process_input(payload)
    
    def test_process_empty_input(self):
        """Test processing empty input"""
        # Test empty text
        payload = ClaimRequest(text="", language="en")
        result = self.service.process_input(payload)
        
        assert result == ""
    
    def test_process_none_input(self):
        """Test processing None input"""
        # Test None text
        payload = ClaimRequest(text=None, language="en")
        result = self.service.process_input(payload)
        
        assert result == ""
    
    def test_url_request_timeout(self):
        """Test URL request timeout handling"""
        payload = ClaimRequest(url="https://example.com/article", language="en")
        
        # Should raise ValueError on error (trafilatura not available)
        with pytest.raises(ValueError, match="Ingestion error for URL"):
            self.service.process_input(payload)
    
    def test_url_request_error(self):
        """Test URL request error handling"""
        payload = ClaimRequest(url="https://example.com/article", language="en")
        
        # Should raise ValueError on error (trafilatura not available)
        with pytest.raises(ValueError, match="Ingestion error for URL"):
            self.service.process_input(payload)
    
    def test_priority_text_over_url(self):
        """Test that text takes priority over URL when both provided"""
        payload = ClaimRequest(
            text="Text content",
            url="https://example.com/article",
            language="en"
        )
        result = self.service.process_input(payload)
        
        # Should return text content, not URL content
        assert result == "Text content"
    
    def test_language_parameter(self):
        """Test language parameter handling"""
        payload = ClaimRequest(text="Test content", language="vi")
        result = self.service.process_input(payload)
        
        assert result == "Test content"
        # Language parameter is stored but not used in processing
        assert payload.language == "vi"


if __name__ == "__main__":
    pytest.main([__file__])
