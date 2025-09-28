"""
Advanced Fallacy Detection Service

Hybrid system combining:
1. Rule-based detection for common fallacies
2. LLM-based detection for complex logical errors
3. Pattern matching for specific fallacy types
4. Explainable AI for user education
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from ..models.report import FallacyItem
from ..core.config import get_settings


class RuleBasedFallacyDetector:
    """Rule-based fallacy detection using pattern matching and linguistic analysis"""
    
    def __init__(self):
        self.fallacy_patterns = self._initialize_fallacy_patterns()
        self.logical_indicators = self._initialize_logical_indicators()
    
    def _initialize_fallacy_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for different types of fallacies"""
        return {
            "hasty_generalization": {
                "patterns": [
                    r"\b(always|never|all|every|none|no one|everyone)\b",
                    r"\b(most|many|some)\s+\w+\s+(always|never|all)\b",
                    r"\b(typical|usually|generally)\s+\w+\s+(always|never)\b"
                ],
                "explanation": "Making broad generalizations from limited evidence",
                "severity": "medium"
            },
            "ad_hominem": {
                "patterns": [
                    r"\b(you're|you are)\s+(stupid|dumb|idiot|moron|ignorant)\b",
                    r"\b(only\s+)?(a\s+)?(fool|idiot|moron)\s+(would|could)\b",
                    r"\b(typical\s+)?(liberal|conservative|republican|democrat)\b",
                    r"\b(you\s+)?(don't|do not)\s+understand\s+(because\s+)?(you're|you are)\b"
                ],
                "explanation": "Attacking the person instead of addressing their argument",
                "severity": "high"
            },
            "straw_man": {
                "patterns": [
                    r"\b(so\s+you're\s+saying|you\s+think|you\s+believe)\s+(that\s+)?(all|every|no|never)\b",
                    r"\b(if\s+)?(we\s+)?(follow\s+your\s+logic|go\s+by\s+what\s+you\s+say)\b",
                    r"\b(according\s+to\s+you|in\s+your\s+view)\s+(all|every|no|never)\b"
                ],
                "explanation": "Misrepresenting someone's argument to make it easier to attack",
                "severity": "high"
            },
            "false_dilemma": {
                "patterns": [
                    r"\b(either|or)\s+(this|that)\s+(or|or else)\s+(this|that)\b",
                    r"\b(you\s+are\s+either|it's\s+either)\s+(with\s+us|against\s+us)\b",
                    r"\b(if\s+you\s+don't|unless\s+you)\s+(support|agree)\s+(then|you)\b"
                ],
                "explanation": "Presenting only two options when more exist",
                "severity": "medium"
            },
            "slippery_slope": {
                "patterns": [
                    r"\b(if\s+we\s+allow|once\s+we\s+start)\s+(this|that)\s+(then|we'll|it will)\b",
                    r"\b(where\s+does\s+it\s+stop|what's\s+next)\b",
                    r"\b(this\s+will\s+lead\s+to|inevitably\s+result\s+in)\b"
                ],
                "explanation": "Assuming one event will inevitably lead to a chain of events",
                "severity": "medium"
            },
            "appeal_to_authority": {
                "patterns": [
                    r"\b(experts|scientists|doctors|professors)\s+(say|agree|believe)\b",
                    r"\b(according\s+to\s+)?(dr\.|prof\.|mr\.|ms\.)\s+\w+\b",
                    r"\b(studies\s+show|research\s+proves|evidence\s+indicates)\b"
                ],
                "explanation": "Using authority as evidence without proper context or expertise",
                "severity": "low"
            },
            "cherry_picking": {
                "patterns": [
                    r"\b(but\s+what\s+about|however|on\s+the\s+other\s+hand)\s+(this|that)\b",
                    r"\b(ignoring|disregarding|overlooking)\s+(the\s+fact\s+that)?\b",
                    r"\b(selective|cherry-picked|conveniently\s+ignoring)\b"
                ],
                "explanation": "Selectively choosing evidence that supports your position",
                "severity": "high"
            },
            "correlation_causation": {
                "patterns": [
                    r"\b(since|because|as)\s+\w+\s+(increased|decreased|changed)\s+(so|therefore|thus)\b",
                    r"\b(correlation|correlates|correlated)\s+(with|to)\b",
                    r"\b(associated\s+with|linked\s+to)\s+(but\s+not\s+caused\s+by)?\b"
                ],
                "explanation": "Assuming correlation implies causation",
                "severity": "medium"
            },
            "appeal_to_emotion": {
                "patterns": [
                    r"\b(think\s+of\s+the\s+children|for\s+the\s+sake\s+of)\b",
                    r"\b(how\s+can\s+you|how\s+dare\s+you)\s+(not|ignore)\b",
                    r"\b(heartless|cruel|selfish|evil)\s+(to\s+)?(not|ignore)\b"
                ],
                "explanation": "Using emotional appeals instead of logical arguments",
                "severity": "medium"
            },
            "red_herring": {
                "patterns": [
                    r"\b(but\s+what\s+about|that's\s+not\s+the\s+point|irrelevant)\b",
                    r"\b(changing\s+the\s+subject|distracting\s+from)\b",
                    r"\b(that's\s+a\s+different\s+issue|off\s+the\s+topic)\b"
                ],
                "explanation": "Introducing irrelevant information to distract from the main issue",
                "severity": "medium"
            }
        }
    
    def _initialize_logical_indicators(self) -> Dict[str, List[str]]:
        """Initialize logical indicators for different fallacy types"""
        return {
            "quantifiers": ["all", "every", "none", "no", "some", "most", "many", "few"],
            "absolutes": ["always", "never", "impossible", "certain", "definitely"],
            "emotional": ["terrible", "awful", "disgusting", "amazing", "incredible"],
            "authority": ["expert", "scientist", "doctor", "professor", "study", "research"],
            "causal": ["because", "since", "therefore", "thus", "consequently", "leads to"],
            "conditional": ["if", "unless", "provided that", "as long as", "in case"]
        }
    
    def detect_fallacies(self, content: str) -> List[FallacyItem]:
        """Detect fallacies using rule-based patterns"""
        fallacies = []
        content_lower = content.lower()
        
        for fallacy_type, config in self.fallacy_patterns.items():
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    # Extract the matched text
                    matched_text = content[match.start():match.end()]
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(pattern, matched_text)
                    
                    if confidence > 0.3:  # Threshold for detection
                        fallacies.append(FallacyItem(
                            type=fallacy_type,
                            span=matched_text,
                            explanation=f"{config['explanation']} (confidence: {confidence:.2f})"
                        ))
        
        # Remove duplicates and sort by confidence
        fallacies = self._deduplicate_fallacies(fallacies)
        return fallacies
    
    def _calculate_pattern_confidence(self, pattern: str, matched_text: str) -> float:
        """Calculate confidence score for a pattern match"""
        base_confidence = 0.5
        
        # Increase confidence for more specific patterns
        if r"\b" in pattern:  # Word boundaries
            base_confidence += 0.2
        
        if len(matched_text.split()) > 2:  # Longer matches
            base_confidence += 0.1
        
        # Decrease confidence for very common words
        common_words = ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        if any(word in matched_text.lower() for word in common_words):
            base_confidence -= 0.1
        
        return min(1.0, max(0.0, base_confidence))
    
    def _deduplicate_fallacies(self, fallacies: List[FallacyItem]) -> List[FallacyItem]:
        """Remove duplicate fallacies and sort by type"""
        seen = set()
        unique_fallacies = []
        
        for fallacy in fallacies:
            key = (fallacy.type, fallacy.span)
            if key not in seen:
                seen.add(key)
                unique_fallacies.append(fallacy)
        
        # Sort by type for consistency
        unique_fallacies.sort(key=lambda x: x.type)
        return unique_fallacies


class LLMBasedFallacyDetector:
    """LLM-based fallacy detection for complex logical errors"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load LLM model for fallacy detection"""
        try:
            # Use a lightweight model for MVP
            model_name = "distilbert-base-uncased"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2,  # Binary: fallacy or not
                device_map="auto" if torch.cuda.is_available() else None
            )
        except Exception as e:
            print(f"Warning: Could not load LLM fallacy detector: {e}")
            self.model = None
            self.tokenizer = None
    
    def detect_fallacies(self, content: str) -> List[FallacyItem]:
        """Detect fallacies using LLM analysis"""
        if self.model is None or self.tokenizer is None:
            return []
        
        try:
            # Simple heuristic-based detection for MVP
            # In production, this would use fine-tuned models on fallacy datasets
            fallacies = []
            
            # Check for complex logical structures
            if self._has_complex_logical_structure(content):
                fallacies.append(FallacyItem(
                    type="complex_logical_error",
                    span=None,
                    explanation="Complex logical structure detected - may contain subtle fallacies"
                ))
            
            # Check for argumentative patterns
            if self._has_argumentative_patterns(content):
                fallacies.append(FallacyItem(
                    type="argumentative_pattern",
                    span=None,
                    explanation="Argumentative patterns detected - may contain logical fallacies"
                ))
            
            return fallacies
        except Exception:
            return []
    
    def _has_complex_logical_structure(self, content: str) -> bool:
        """Check if content has complex logical structure"""
        logical_indicators = [
            "therefore", "thus", "consequently", "hence", "so",
            "because", "since", "as", "given that", "in light of",
            "if", "unless", "provided that", "assuming that"
        ]
        
        content_lower = content.lower()
        logical_count = sum(1 for indicator in logical_indicators if indicator in content_lower)
        
        # Consider complex if it has multiple logical indicators
        return logical_count >= 3
    
    def _has_argumentative_patterns(self, content: str) -> bool:
        """Check if content has argumentative patterns"""
        argumentative_indicators = [
            "argue", "claim", "assert", "maintain", "contend",
            "evidence", "proof", "demonstrate", "show", "prove",
            "however", "nevertheless", "on the other hand", "in contrast"
        ]
        
        content_lower = content.lower()
        argumentative_count = sum(1 for indicator in argumentative_indicators if indicator in content_lower)
        
        return argumentative_count >= 2


class FallacyDetector:
    """Main fallacy detection service combining rule-based and LLM approaches"""
    
    def __init__(self):
        self.rule_detector = RuleBasedFallacyDetector()
        self.llm_detector = LLMBasedFallacyDetector()
        self.fallacy_severity = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4
        }
    
    def detect(self, content: str) -> list[FallacyItem]:
        """Detect fallacies using hybrid approach"""
        if not content or len(content.strip()) < 10:
            return []
        
        # Rule-based detection
        rule_fallacies = self.rule_detector.detect_fallacies(content)
        
        # LLM-based detection
        llm_fallacies = self.llm_detector.detect_fallacies(content)
        
        # Combine and prioritize results
        all_fallacies = rule_fallacies + llm_fallacies
        
        # Remove duplicates and sort by severity
        unique_fallacies = self._deduplicate_and_rank(all_fallacies)
        
        # Limit to top 5 most relevant fallacies
        return unique_fallacies[:5]
    
    def _deduplicate_and_rank(self, fallacies: List[FallacyItem]) -> List[FallacyItem]:
        """Remove duplicates and rank by severity and relevance"""
        # Group by type
        fallacy_groups = {}
        for fallacy in fallacies:
            if fallacy.type not in fallacy_groups:
                fallacy_groups[fallacy.type] = []
            fallacy_groups[fallacy.type].append(fallacy)
        
        # Select best representative for each type
        ranked_fallacies = []
        for fallacy_type, group in fallacy_groups.items():
            # Sort by explanation quality (longer explanations are usually better)
            best_fallacy = max(group, key=lambda x: len(x.explanation or ""))
            ranked_fallacies.append(best_fallacy)
        
        # Sort by severity (high -> medium -> low)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        ranked_fallacies.sort(key=lambda x: severity_order.get(
            self._get_fallacy_severity(x.type), 2
        ))
        
        return ranked_fallacies
    
    def _get_fallacy_severity(self, fallacy_type: str) -> str:
        """Get severity level for a fallacy type"""
        severity_map = {
            "ad_hominem": "high",
            "straw_man": "high", 
            "cherry_picking": "high",
            "hasty_generalization": "medium",
            "false_dilemma": "medium",
            "slippery_slope": "medium",
            "correlation_causation": "medium",
            "appeal_to_emotion": "medium",
            "red_herring": "medium",
            "appeal_to_authority": "low",
            "complex_logical_error": "medium",
            "argumentative_pattern": "low"
        }
        return severity_map.get(fallacy_type, "low")



