"""
Unit tests for AIDetectionService

Tests:
1. RoBERTa-based detection
2. Stylometry analysis
3. Metadata checks
4. Ensemble voting
5. Noise injection
6. Multi-signal detection
"""

import pytest
from unittest.mock import Mock, patch
from app.services.ai_detection_service import AIDetectionService


class TestAIDetectionService:
    """Test suite for AIDetectionService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = AIDetectionService()
    
    def test_roberta_detection(self):
        """Test RoBERTa-based AI detection"""
        content = "This is a test content for AI detection."
        
        with patch.object(self.service, '_load_roberta_detector') as mock_roberta:
            mock_pipeline = Mock()
            mock_pipeline.return_value = [{"label": "AI", "score": 0.8}]
            mock_roberta.return_value = mock_pipeline
            
            result = self.service._roberta_detection(content)
            
            assert result is not None
            assert "score" in result
            assert "label" in result
    
    def test_roberta_detection_fallback(self):
        """Test RoBERTa detection fallback when model not available"""
        content = "This is a test content for AI detection."
        
        with patch.object(self.service, '_load_roberta_detector', return_value=None):
            result = self.service._roberta_detection(content)
            
            # Should return fallback result
            assert result is not None
            assert result["score"] == 0.5
            assert result["label"] == "UNKNOWN"
    
    def test_stylometry_analysis(self):
        """Test stylometry analysis"""
        content = "This is a test content for stylometry analysis. It contains multiple sentences to analyze."
        
        result = self.service._stylometry_analysis(content)
        
        assert result is not None
        assert "score" in result
        assert "features" in result
        assert isinstance(result["features"], dict)
    
    def test_metadata_checks(self):
        """Test metadata checks"""
        content = "This is a test content."
        metadata = {
            "source": "user_input",
            "timestamp": "2024-01-01T00:00:00Z",
            "user_agent": "Mozilla/5.0"
        }
        
        result = self.service._metadata_checks(content, metadata)
        
        assert result is not None
        assert "score" in result
        assert "checks" in result
        assert isinstance(result["checks"], dict)
    
    def test_metadata_checks_no_metadata(self):
        """Test metadata checks with no metadata"""
        content = "This is a test content."
        
        result = self.service._metadata_checks(content, None)
        
        assert result is not None
        assert "score" in result
        assert "checks" in result
    
    def test_ensemble_voting(self):
        """Test ensemble voting mechanism"""
        scores = {
            "roberta": 0.8,
            "stylometry": 0.6,
            "metadata": 0.4
        }
        
        result = self.service._ensemble_voting(scores)
        
        assert result is not None
        assert "final_score" in result
        assert "method" in result
        assert "weights" in result
        assert isinstance(result["weights"], dict)
    
    def test_noise_injection(self):
        """Test noise injection for robustness"""
        content = "This is a test content for noise injection."
        
        result = self.service._noise_injection(content)
        
        assert result is not None
        assert "original_content" in result
        assert "noisy_content" in result
        assert "noise_type" in result
        assert result["original_content"] == content
    
    def test_detect_ai_generated_basic(self):
        """Test basic AI detection"""
        content = "This is a test content for AI detection."
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
        assert "method" in result
        assert "scores" in result
        assert "details" in result
        
        assert isinstance(result["is_ai_generated"], bool)
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["method"] == "multi_signal_ensemble"
    
    def test_detect_ai_generated_with_metadata(self):
        """Test AI detection with metadata"""
        content = "This is a test content for AI detection."
        metadata = {
            "source": "user_input",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        result = self.service.detect_ai_generated(content, metadata)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
        assert "method" in result
        assert "scores" in result
        assert "details" in result
    
    def test_detect_ai_generated_empty_content(self):
        """Test AI detection with empty content"""
        content = ""
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
        assert result["confidence"] == 0.5  # Default confidence for empty content
    
    def test_detect_ai_generated_short_content(self):
        """Test AI detection with very short content"""
        content = "Hi"
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
        assert result["confidence"] == 0.5  # Default confidence for short content
    
    def test_detect_ai_generated_long_content(self):
        """Test AI detection with long content"""
        content = "This is a very long content that contains many sentences and should be processed normally by the AI detection service. " * 10
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
        assert "method" in result
        assert "scores" in result
        assert "details" in result
    
    def test_detect_ai_generated_special_characters(self):
        """Test AI detection with special characters"""
        content = "This is a test with special characters: @#$%^&*()_+-=[]{}|;':\",./<>?"
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
    
    def test_detect_ai_generated_unicode(self):
        """Test AI detection with unicode characters"""
        content = "This is a test with unicode: 你好世界 🌍 émojis"
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
    
    def test_detect_ai_generated_multilingual(self):
        """Test AI detection with multilingual content"""
        content = "This is English. Esto es español. C'est français. 这是中文."
        
        result = self.service.detect_ai_generated(content)
        
        assert result is not None
        assert "is_ai_generated" in result
        assert "confidence" in result
    
    def test_detect_ai_generated_error_handling(self):
        """Test AI detection error handling"""
        content = "This is a test content."
        
        with patch.object(self.service, '_roberta_detection', side_effect=Exception("Test error")):
            result = self.service.detect_ai_generated(content)
            
            # Should still return a result despite error
            assert result is not None
            assert "is_ai_generated" in result
            assert "confidence" in result
    
    def test_detect_ai_generated_consistency(self):
        """Test AI detection consistency"""
        content = "This is a test content for consistency testing."
        
        # Run detection multiple times
        results = []
        for _ in range(3):
            result = self.service.detect_ai_generated(content)
            results.append(result)
        
        # Results should be consistent (same structure)
        for result in results:
            assert "is_ai_generated" in result
            assert "confidence" in result
            assert "method" in result
            assert "scores" in result
            assert "details" in result
    
    def test_detect_ai_generated_threshold(self):
        """Test AI detection threshold behavior"""
        content = "This is a test content."
        
        result = self.service.detect_ai_generated(content)
        
        # Check threshold behavior
        if result["confidence"] > 0.7:
            assert result["is_ai_generated"] == True
        elif result["confidence"] < 0.3:
            assert result["is_ai_generated"] == False
        else:
            # In between, could be either
            assert isinstance(result["is_ai_generated"], bool)


if __name__ == "__main__":
    pytest.main([__file__])

