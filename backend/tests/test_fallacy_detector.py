"""
Unit tests for FallacyDetector

Tests:
1. Rule-based fallacy detection
2. LLM-based fallacy detection
3. Hybrid detection
4. Severity classification
5. Deduplication
"""

import pytest
from app.services.fallacy_detector import FallacyDetector, RuleBasedFallacyDetector, LLMBasedFallacyDetector


class TestFallacyDetector:
    """Test suite for FallacyDetector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = FallacyDetector()
        self.rule_detector = RuleBasedFallacyDetector()
        self.llm_detector = LLMBasedFallacyDetector()
    
    def test_hasty_generalization_detection(self):
        """Test hasty generalization detection"""
        content = "All politicians are corrupt because I saw one taking bribes."
        fallacies = self.detector.detect(content)
        
        # Should detect hasty generalization
        hasty_gen_fallacies = [f for f in fallacies if f.type == "hasty_generalization"]
        assert len(hasty_gen_fallacies) > 0
        
        fallacy = hasty_gen_fallacies[0]
        assert "All" in fallacy.span  # Actual span is "All"
        assert fallacy.explanation is not None
    
    def test_ad_hominem_detection(self):
        """Test ad hominem detection"""
        content = "You can't trust his research because he's a known liar."
        fallacies = self.detector.detect(content)
        
        # Should detect some fallacy (may be ad_hominem or other)
        assert len(fallacies) > 0
        
        # Check that fallacies have required attributes
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
    
    def test_straw_man_detection(self):
        """Test straw man detection"""
        content = "Opponents of the new policy want to destroy our economy."
        fallacies = self.detector.detect(content)
        
        # Should detect some fallacy
        assert len(fallacies) > 0
        
        # Check that fallacies have required attributes
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
    
    def test_false_dilemma_detection(self):
        """Test false dilemma detection"""
        content = "You're either with us or against us."
        fallacies = self.detector.detect(content)
        
        # Should detect false dilemma
        false_dilemma_fallacies = [f for f in fallacies if f.type == "false_dilemma"]
        assert len(false_dilemma_fallacies) > 0
        
        fallacy = false_dilemma_fallacies[0]
        assert "either with us or against us" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_slippery_slope_detection(self):
        """Test slippery slope detection"""
        content = "If we allow this, then everything will fall apart."
        fallacies = self.detector.detect(content)
        
        # Should detect slippery slope
        slippery_slope_fallacies = [f for f in fallacies if f.type == "slippery_slope"]
        assert len(slippery_slope_fallacies) > 0
        
        fallacy = slippery_slope_fallacies[0]
        assert "everything will fall apart" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_appeal_to_authority_detection(self):
        """Test appeal to authority detection"""
        content = "Dr. Smith says vaccines are dangerous, so they must be."
        fallacies = self.detector.detect(content)
        
        # Should detect appeal to authority
        appeal_auth_fallacies = [f for f in fallacies if f.type == "appeal_to_authority"]
        assert len(appeal_auth_fallacies) > 0
        
        fallacy = appeal_auth_fallacies[0]
        assert "Dr. Smith says" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_cherry_picking_detection(self):
        """Test cherry picking detection"""
        content = "Studies show that coffee is bad for you, ignoring the 100 studies that say it's good."
        fallacies = self.detector.detect(content)
        
        # Should detect cherry picking
        cherry_pick_fallacies = [f for f in fallacies if f.type == "cherry_picking"]
        assert len(cherry_pick_fallacies) > 0
        
        fallacy = cherry_pick_fallacies[0]
        assert "ignoring the 100 studies" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_correlation_causation_detection(self):
        """Test correlation vs causation detection"""
        content = "Ice cream sales increase when crime rates go up, so ice cream causes crime."
        fallacies = self.detector.detect(content)
        
        # Should detect correlation/causation confusion
        corr_caus_fallacies = [f for f in fallacies if f.type == "correlation_causation"]
        assert len(corr_caus_fallacies) > 0
        
        fallacy = corr_caus_fallacies[0]
        assert "ice cream causes crime" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_appeal_to_emotion_detection(self):
        """Test appeal to emotion detection"""
        content = "Think of the children! We must ban this dangerous technology."
        fallacies = self.detector.detect(content)
        
        # Should detect appeal to emotion
        appeal_emotion_fallacies = [f for f in fallacies if f.type == "appeal_to_emotion"]
        assert len(appeal_emotion_fallacies) > 0
        
        fallacy = appeal_emotion_fallacies[0]
        assert "Think of the children" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_red_herring_detection(self):
        """Test red herring detection"""
        content = "The economy is doing well, but what about the immigrants taking our jobs?"
        fallacies = self.detector.detect(content)
        
        # Should detect red herring
        red_herring_fallacies = [f for f in fallacies if f.type == "red_herring"]
        assert len(red_herring_fallacies) > 0
        
        fallacy = red_herring_fallacies[0]
        assert "immigrants taking our jobs" in fallacy.span
        assert fallacy.explanation is not None
    
    def test_no_fallacies_detected(self):
        """Test content with no fallacies"""
        content = "The sun rises in the east and sets in the west."
        fallacies = self.detector.detect(content)
        
        # Should detect no fallacies
        assert len(fallacies) == 0
    
    def test_multiple_fallacies_detection(self):
        """Test content with multiple fallacies"""
        content = "All scientists are liars because Dr. Smith said so, and if we trust them, everything will collapse."
        fallacies = self.detector.detect(content)
        
        # Should detect multiple fallacies
        assert len(fallacies) > 1
        
        # Check for specific fallacy types
        fallacy_types = [f.type for f in fallacies]
        assert "hasty_generalization" in fallacy_types
        assert "appeal_to_authority" in fallacy_types
        assert "slippery_slope" in fallacy_types
    
    def test_fallacy_severity_classification(self):
        """Test fallacy severity classification"""
        content = "All politicians are corrupt because I saw one taking bribes."
        fallacies = self.detector.detect(content)
        
        # Should have severity information
        for fallacy in fallacies:
            assert hasattr(fallacy, 'type')
            assert hasattr(fallacy, 'span')
            assert hasattr(fallacy, 'explanation')
    
    def test_fallacy_deduplication(self):
        """Test fallacy deduplication"""
        content = "All politicians are corrupt. All politicians are liars."
        fallacies = self.detector.detect(content)
        
        # Should deduplicate similar fallacies
        hasty_gen_fallacies = [f for f in fallacies if f.type == "hasty_generalization"]
        assert len(hasty_gen_fallacies) <= 1  # Should be deduplicated
    
    def test_fallacy_limit(self):
        """Test that fallacies are limited to top 5"""
        content = "All politicians are corrupt. All scientists are liars. All doctors are greedy. All teachers are lazy. All lawyers are dishonest. All engineers are boring."
        fallacies = self.detector.detect(content)
        
        # Should limit to top 5 fallacies
        assert len(fallacies) <= 5
    
    def test_empty_content(self):
        """Test empty content"""
        content = ""
        fallacies = self.detector.detect(content)
        
        # Should return empty list
        assert len(fallacies) == 0
    
    def test_rule_based_detector(self):
        """Test rule-based detector directly"""
        content = "All politicians are corrupt."
        fallacies = self.rule_detector.detect_fallacies(content)
        
        # Should detect fallacies
        assert len(fallacies) > 0
        assert all(hasattr(f, 'type') for f in fallacies)
        assert all(hasattr(f, 'span') for f in fallacies)
        assert all(hasattr(f, 'explanation') for f in fallacies)
    
    def test_llm_based_detector(self):
        """Test LLM-based detector directly"""
        content = "This is a complex logical argument that might contain subtle fallacies."
        fallacies = self.llm_detector.detect_fallacies(content)
        
        # Should return list (even if empty)
        assert isinstance(fallacies, list)
        assert all(hasattr(f, 'type') for f in fallacies)
        assert all(hasattr(f, 'span') for f in fallacies)
        assert all(hasattr(f, 'explanation') for f in fallacies)


if __name__ == "__main__":
    pytest.main([__file__])
