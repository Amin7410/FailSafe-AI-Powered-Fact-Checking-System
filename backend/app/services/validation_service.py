"""
Report Validation Service

Validates report structure and content against schemas.
"""

import jsonschema
from typing import Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ReportValidator:
    """Service for validating report structure and content"""
    
    def __init__(self):
        self.schema = self._load_report_schema()
    
    def _load_report_schema(self) -> Dict[str, Any]:
        """Load JSON schema for report validation"""
        return {
            "type": "object",
            "required": [
                "claim_id", "timestamp", "input_text", "verdict", 
                "confidence", "evidence", "verification", "fallacies"
            ],
            "properties": {
                "claim_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "input_text": {"type": "string", "minLength": 1},
                "input_url": {"type": ["string", "null"]},
                "verdict": {
                    "type": "string",
                    "enum": ["True", "False", "Mixed", "Unverifiable"]
                },
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["source", "relevance_score", "credibility_score"],
                        "properties": {
                            "source": {"type": "string"},
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "relevance_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "credibility_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "content": {"type": "string"},
                            "metadata": {"type": "object"}
                        }
                    }
                },
                "verification": {
                    "type": "object",
                    "required": ["is_verified", "confidence", "reasoning"],
                    "properties": {
                        "is_verified": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "reasoning": {"type": "string"},
                        "sources_checked": {"type": "integer", "minimum": 0},
                        "contradictory_sources": {"type": "integer", "minimum": 0},
                        "supporting_sources": {"type": "integer", "minimum": 0},
                        "metadata": {"type": "object"}
                    }
                },
                "fallacies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "description", "confidence"],
                        "properties": {
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "location": {"type": "string"},
                            "suggestion": {"type": "string"},
                            "metadata": {"type": "object"}
                        }
                    }
                },
                "sag": {"type": "object"},
                "multilingual_data": {"type": ["object", "null"]},
                "ai_detection": {"type": ["object", "null"]},
                "processing_time_ms": {"type": "integer", "minimum": 0},
                "metadata": {"type": "object"}
            }
        }
    
    def validate(self, report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate report against schema
        
        Args:
            report_data: Report data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            # Validate against JSON schema
            jsonschema.validate(report_data, self.schema)
            
            # Additional business logic validation
            business_errors = self._validate_business_logic(report_data)
            
            if business_errors:
                return False, business_errors
            
            logger.info("Report validation successful")
            return True, []
            
        except jsonschema.ValidationError as e:
            error_msg = f"Schema validation error: {e.message}"
            logger.warning(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def _validate_business_logic(self, report_data: Dict[str, Any]) -> List[str]:
        """Validate business logic rules"""
        errors = []
        
        try:
            # Check confidence consistency
            confidence = report_data.get("confidence", 0.0)
            verdict = report_data.get("verdict", "")
            
            if verdict == "True" and confidence < 0.6:
                errors.append("True verdict with low confidence is suspicious")
            
            if verdict == "False" and confidence < 0.6:
                errors.append("False verdict with low confidence is suspicious")
            
            # Check evidence quality
            evidence = report_data.get("evidence", [])
            if evidence:
                avg_relevance = sum(
                    e.get("relevance_score", 0.0) for e in evidence
                ) / len(evidence)
                
                if avg_relevance < 0.3:
                    errors.append("Evidence has very low average relevance")
            
            # Check verification consistency
            verification = report_data.get("verification", {})
            is_verified = verification.get("is_verified", False)
            verification_confidence = verification.get("confidence", 0.0)
            
            if is_verified and verification_confidence < 0.5:
                errors.append("Verified claim with low verification confidence")
            
            # Check fallacy consistency
            fallacies = report_data.get("fallacies", [])
            high_confidence_fallacies = [
                f for f in fallacies if f.get("confidence", 0.0) > 0.8
            ]
            
            if high_confidence_fallacies and verdict == "True":
                errors.append("True verdict despite high-confidence fallacies detected")
            
        except Exception as e:
            errors.append(f"Business logic validation error: {str(e)}")
        
        return errors
    
    def validate_evidence(self, evidence: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate evidence items"""
        errors = []
        
        for i, item in enumerate(evidence):
            try:
                # Check required fields
                if not item.get("source"):
                    errors.append(f"Evidence item {i}: Missing source")
                
                if not isinstance(item.get("relevance_score"), (int, float)):
                    errors.append(f"Evidence item {i}: Invalid relevance_score")
                elif not 0.0 <= item.get("relevance_score", 0) <= 1.0:
                    errors.append(f"Evidence item {i}: Relevance score out of range")
                
                if not isinstance(item.get("credibility_score"), (int, float)):
                    errors.append(f"Evidence item {i}: Invalid credibility_score")
                elif not 0.0 <= item.get("credibility_score", 0) <= 1.0:
                    errors.append(f"Evidence item {i}: Credibility score out of range")
                
            except Exception as e:
                errors.append(f"Evidence item {i}: Validation error - {str(e)}")
        
        return len(errors) == 0, errors
    
    def validate_fallacies(self, fallacies: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate fallacy items"""
        errors = []
        
        for i, fallacy in enumerate(fallacies):
            try:
                # Check required fields
                if not fallacy.get("type"):
                    errors.append(f"Fallacy item {i}: Missing type")
                
                if not fallacy.get("description"):
                    errors.append(f"Fallacy item {i}: Missing description")
                
                if not isinstance(fallacy.get("confidence"), (int, float)):
                    errors.append(f"Fallacy item {i}: Invalid confidence")
                elif not 0.0 <= fallacy.get("confidence", 0) <= 1.0:
                    errors.append(f"Fallacy item {i}: Confidence out of range")
                
            except Exception as e:
                errors.append(f"Fallacy item {i}: Validation error - {str(e)}")
        
        return len(errors) == 0, errors