"""
Simplified unit tests for FallacyDetector

Tests core functionality without exact pattern matching
"""

import pytest
from app.services.fallacy_detector import FallacyDetector


class TestFallacyDetectorSimple:
    """Simplified test suite for FallacyDetector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = FallacyDetector()
    
    def test_detector_initialization(self):
        """Test that detector initializes properly"""
        assert self.detector is not None
        assert hasattr(self.detector, 'detect')
        assert hasattr(self.detector, 'rule_detector')
        assert hasattr(self.detector, 'llm_detector')
    
    def test_detect_returns_list(self):
        """Test that detect method returns a list"""
        content = "This is a test content."
        result = self.detector.detect(content)
        
        assert isinstance(result, list)
    
    def test_detect_with_fallacy_content(self):
        """Test detection with content that should contain fallacies"""
        content = "All politicians are corrupt because I saw one taking bribes."
        fallacies = self.detector.detect(content)
        
        # Should detect at least one fallacy
        assert len(fallacies) > 0
        
        # Check that all fallacies have required attributes
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
            assert isinstance(fallacy.type, str)
            assert isinstance(fallacy.span, str)
            assert isinstance(fallacy.explanation, str)
    
    def test_detect_with_no_fallacy_content(self):
        """Test detection with content that should not contain fallacies"""
        content = "The sun rises in the east and sets in the west."
        fallacies = self.detector.detect(content)
        
        # Should detect no fallacies or very few
        assert len(fallacies) <= 1  # Allow for some false positives
    
    def test_detect_with_empty_content(self):
        """Test detection with empty content"""
        content = ""
        fallacies = self.detector.detect(content)
        
        # Should return empty list
        assert len(fallacies) == 0
    
    def test_detect_with_short_content(self):
        """Test detection with very short content"""
        content = "Hi"
        fallacies = self.detector.detect(content)
        
        # Should return empty list or very few fallacies
        assert len(fallacies) <= 1
    
    def test_detect_with_long_content(self):
        """Test detection with long content"""
        content = "This is a very long content that contains many sentences and should be processed normally by the fallacy detection service. " * 10
        fallacies = self.detector.detect(content)
        
        # Should return a list (may be empty or contain fallacies)
        assert isinstance(fallacies, list)
        
        # Check that all fallacies have required attributes
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
    
    def test_detect_consistency(self):
        """Test that detection is consistent"""
        content = "All politicians are corrupt."
        
        # Run detection multiple times
        results = []
        for _ in range(3):
            result = self.detector.detect(content)
            results.append(result)
        
        # Results should be consistent (same structure)
        for result in results:
            assert isinstance(result, list)
            for fallacy in result:
                assert hasattr(fallacy, 'type')
                assert hasattr(fallacy, 'span')
                assert hasattr(fallacy, 'explanation')
    
    def test_detect_with_special_characters(self):
        """Test detection with special characters"""
        content = "This is a test with special characters: @#$%^&*()_+-=[]{}|;':\",./<>?"
        fallacies = self.detector.detect(content)
        
        # Should return a list
        assert isinstance(fallacies, list)
    
    def test_detect_with_unicode(self):
        """Test detection with unicode characters"""
        content = "This is a test with unicode: 你好世界 🌍 émojis"
        fallacies = self.detector.detect(content)
        
        # Should return a list
        assert isinstance(fallacies, list)
    
    def test_detect_multiple_fallacies(self):
        """Test detection with content that should contain multiple fallacies"""
        content = "All scientists are liars because Dr. Smith said so, and if we trust them, everything will collapse."
        fallacies = self.detector.detect(content)
        
        # Should detect multiple fallacies
        assert len(fallacies) > 1
        
        # Check that all fallacies have required attributes
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
    
    def test_fallacy_limit(self):
        """Test that fallacies are limited to top 5"""
        content = "All politicians are corrupt. All scientists are liars. All doctors are greedy. All teachers are lazy. All lawyers are dishonest. All engineers are boring."
        fallacies = self.detector.detect(content)
        
        # Should limit to top 5 fallacies
        assert len(fallacies) <= 5
    
    def test_rule_based_detector(self):
        """Test rule-based detector directly"""
        content = "All politicians are corrupt."
        fallacies = self.detector.rule_detector.detect_fallacies(content)
        
        # Should detect fallacies
        assert len(fallacies) > 0
        assert all(hasattr(f, 'type') for f in fallacies)
        assert all(hasattr(f, 'span') for f in fallacies)
        assert all(hasattr(f, 'explanation') for f in fallacies)
    
    def test_llm_based_detector(self):
        """Test LLM-based detector directly"""
        content = "This is a complex logical argument that might contain subtle fallacies."
        fallacies = self.detector.llm_detector.detect_fallacies(content)
        
        # Should return list (even if empty)
        assert isinstance(fallacies, list)
        assert all(hasattr(f, 'type') for f in fallacies)
        assert all(hasattr(f, 'span') for f in fallacies)
        assert all(hasattr(f, 'explanation') for f in fallacies)


if __name__ == "__main__":
    pytest.main([__file__])

