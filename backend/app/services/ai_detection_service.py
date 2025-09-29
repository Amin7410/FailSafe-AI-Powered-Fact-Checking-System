"""
AI Detection Service

Detects AI-generated content using multiple signals and ensemble methods.
"""

import logging
from typing import Dict, Any, Optional
import re
import statistics

logger = logging.getLogger(__name__)


class AIDetectionService:
    """Service for detecting AI-generated content"""
    
    def __init__(self):
        self.detection_methods = [
            "stylometry",
            "metadata_check", 
            "pattern_analysis",
            "llm_detector"
        ]
    
    def detect_ai_generated(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect if content is AI-generated
        
        Args:
            content: Text content to analyze
            metadata: Optional metadata
            
        Returns:
            Dict containing detection results
        """
        try:
            # Initialize results
            results = {
                "is_ai_generated": False,
                "confidence": 0.0,
                "method": "ensemble",
                "scores": {},
                "details": {}
            }
            
            # Run detection methods
            method_scores = {}
            
            # 1. Stylometry analysis
            stylometry_score = self._analyze_stylometry(content)
            method_scores["stylometry"] = stylometry_score
            
            # 2. Metadata check
            metadata_score = self._check_metadata(metadata)
            method_scores["metadata"] = metadata_score
            
            # 3. Pattern analysis
            pattern_score = self._analyze_patterns(content)
            method_scores["pattern"] = pattern_score
            
            # 4. LLM detector (simplified)
            llm_score = self._llm_detection(content)
            method_scores["llm_detector"] = llm_score

            # 5. Noise-injection stability (simple paraphrase/remove punctuation test)
            stability_score = self._noise_injection_stability(content)
            method_scores["stability"] = stability_score
            
            # Ensemble voting
            ensemble_score = statistics.mean(method_scores.values())
            
            # Determine if AI-generated
            threshold = 0.6
            is_ai_generated = ensemble_score > threshold
            
            # Update results
            results.update({
                "is_ai_generated": is_ai_generated,
                "confidence": ensemble_score,
                "scores": method_scores,
                "details": {
                    "threshold": threshold,
                    "method_count": len(method_scores),
                    "content_length": len(content)
                }
            })
            
            logger.info(f"AI detection completed: {is_ai_generated} (confidence: {ensemble_score:.3f})")
            return results
            
        except Exception as e:
            logger.error(f"Error in AI detection: {e}")
            return {
                "is_ai_generated": False,
                "confidence": 0.0,
                "method": "error",
                "scores": {},
                "details": {"error": str(e)}
            }
    
    def _analyze_stylometry(self, content: str) -> float:
        """Analyze writing style characteristics"""
        try:
            score = 0.0
            
            # Check for repetitive patterns
            sentences = content.split('.')
            if len(sentences) > 1:
                avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
                if 15 <= avg_length <= 25:  # Typical AI sentence length
                    score += 0.3
            
            # Check for formal language patterns
            formal_patterns = [
                r'\b(Furthermore|Moreover|Additionally|In conclusion)\b',
                r'\b(It is important to note|It should be noted)\b',
                r'\b(As we can see|As mentioned above)\b'
            ]
            
            formal_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in formal_patterns)
            if formal_count > 2:
                score += 0.2
            
            # Check for lack of personal pronouns
            personal_pronouns = len(re.findall(r'\b(I|me|my|we|us|our)\b', content, re.IGNORECASE))
            if personal_pronouns < 2 and len(content.split()) > 50:
                score += 0.2
            
            # Check for perfect grammar (AI tends to be very formal)
            if not re.search(r'\b(um|uh|like|you know)\b', content, re.IGNORECASE):
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"Stylometry analysis error: {e}")
            return 0.0
    
    def _check_metadata(self, metadata: Optional[Dict[str, Any]]) -> float:
        """Check metadata for AI generation indicators"""
        if not metadata:
            return 0.0
        
        score = 0.0
        
        # Check for AI-related metadata
        ai_indicators = [
            'generated_by_ai',
            'ai_model',
            'gpt',
            'claude',
            'llm'
        ]
        
        metadata_str = str(metadata).lower()
        for indicator in ai_indicators:
            if indicator in metadata_str:
                score += 0.3
        
        return min(1.0, score)
    
    def _analyze_patterns(self, content: str) -> float:
        """Analyze content patterns"""
        try:
            score = 0.0
            
            # Check for repetitive sentence structures
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            if len(sentences) > 3:
                # Check for similar sentence starts
                starts = [s.split()[0].lower() for s in sentences if s.split()]
                if len(set(starts)) < len(starts) * 0.7:  # Too many similar starts
                    score += 0.3
            
            # Check for AI-typical phrases
            ai_phrases = [
                r'\b(It is worth noting|It should be noted|It is important to)\b',
                r'\b(Furthermore|Moreover|Additionally)\b',
                r'\b(In conclusion|To summarize|Overall)\b',
                r'\b(It is clear that|It is evident that)\b'
            ]
            
            phrase_count = sum(len(re.findall(phrase, content, re.IGNORECASE)) for phrase in ai_phrases)
            if phrase_count > 1:
                score += min(0.4, phrase_count * 0.1)
            
            # Check for lack of contractions
            contractions = len(re.findall(r'\b(don\'t|won\'t|can\'t|isn\'t|aren\'t)\b', content, re.IGNORECASE))
            if contractions == 0 and len(content.split()) > 30:
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"Pattern analysis error: {e}")
            return 0.0
    
    def _llm_detection(self, content: str) -> float:
        """Simplified LLM-based detection"""
        try:
            score = 0.0
            
            # Check for typical AI response patterns
            if content.startswith(('Based on', 'According to', 'It appears that')):
                score += 0.3
            
            # Check for balanced, neutral tone
            if not re.search(r'[!]{2,}|[?]{2,}', content):  # No excessive punctuation
                score += 0.1
            
            # Check for comprehensive coverage (AI tends to be thorough)
            if len(content.split()) > 100 and 'however' in content.lower():
                score += 0.2
            
            # Check for lack of personal experience indicators
            personal_indicators = ['I remember', 'I experienced', 'I saw', 'I heard']
            if not any(indicator in content for indicator in personal_indicators):
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"LLM detection error: {e}")
            return 0.0

    def _noise_injection_stability(self, content: str) -> float:
        """Apply a simple perturbation and compare heuristic signals.

        If detection signals stay similar after perturbation, increase AI likelihood slightly.
        """
        try:
            if not content or len(content.split()) < 20:
                return 0.0
            # Perturbation: remove punctuation and lowercase
            import re as _re
            perturbed = _re.sub(r"[\.,;:!?]", "", content).lower()
            s1 = self._analyze_stylometry(content)
            s2 = self._analyze_stylometry(perturbed)
            p1 = self._analyze_patterns(content)
            p2 = self._analyze_patterns(perturbed)
            delta = abs((s1 + p1) - (s2 + p2))
            # Smaller delta => more stable => more likely AI (return inverse)
            return float(max(0.0, min(1.0, 1.0 - min(1.0, delta))))
        except Exception as e:
            logger.warning(f"Stability check error: {e}")
            return 0.0






