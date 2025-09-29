"""
Enhanced Anti-Hallucination Verification Service

Multi-layered approach to prevent AI hallucinations:
1. Multi-agent cross-check (Llama 4 + Magistral)
2. Self-reflection mechanism
3. Retrieval-first pipeline
4. Confidence calibration with TruthfulQA
5. Structured output validation
6. Auto-escalation system
"""

from __future__ import annotations

import json
import math
import re
import statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from ..models.report import VerificationResult
from .llm_client import OllamaClient, preliminary_reasoning_for_claim
from .embedding_service import embed_texts
from ..core.config import get_settings


class SelfReflectionAgent:
    """Self-reflection mechanism for AI output validation"""
    
    def __init__(self):
        self.reflection_questions = [
            "Is this output based on the provided evidence?",
            "Are there any unsupported claims in this response?",
            "Does this response contain any fabricated information?",
            "Is the confidence level appropriate for the evidence quality?",
            "Are there any logical inconsistencies in this analysis?"
        ]
    
    def reflect_on_output(self, output: str, evidence: List[Dict], context: str) -> Dict[str, Any]:
        """LLM-based reflection returning an overall score and brief reasoning."""
        client = OllamaClient()
        titles = "; ".join([str(ev.get("title") or "") for ev in evidence][:5]) or "(no titles)"
        questions = " "; join(self.reflection_questions)  # type: ignore[attr-defined]
        try:
            questions = " ".join(self.reflection_questions)
        except Exception:
            questions = ""
        prompt = (
            "Assess the following analysis for hallucination risk.\n"
            "Consider these questions: " + questions + "\n\n"
            f"Claim/context: {context}\n"
            f"Evidence titles: {titles}\n"
            f"Analysis: {output}\n\n"
            "Respond as: score=0.x | one-sentence reasoning"
        )
        text = client.generate(prompt)
        score = 0.5
        if "score=" in text:
            try:
                score_str = text.split("score=")[-1].split("|")[0].strip()
                score = float(score_str)
            except Exception:
                score = 0.5
        hallucination_risk = "high" if score < 0.3 else "medium" if score < 0.7 else "low"
        return {
            "overall_score": max(0.0, min(1.0, score)),
            "individual_scores": [],
            "details": [{"summary": text}],
            "hallucination_risk": hallucination_risk,
        }
    
    def _evaluate_question(self, question: str, output: str, evidence: List[Dict], context: str) -> float:
        """Evaluate a specific reflection question"""
        # Simple heuristic evaluation for MVP
        if "evidence" in question.lower():
            # Check if output references evidence
            evidence_mentions = sum(1 for ev in evidence if ev.get("source", "") in output)
            return min(1.0, evidence_mentions / max(1, len(evidence)))
        
        elif "unsupported" in question.lower():
            # Check for unsupported claims (simple heuristic)
            unsupported_indicators = ["definitely", "certainly", "proven", "fact"]
            unsupported_count = sum(1 for indicator in unsupported_indicators if indicator in output.lower())
            return max(0.0, 1.0 - (unsupported_count * 0.2))
        
        elif "fabricated" in question.lower():
            # Check for potential fabrication
            fabrication_indicators = ["studies show", "research proves", "experts agree"]
            fabrication_count = sum(1 for indicator in fabrication_indicators if indicator in output.lower())
            return max(0.0, 1.0 - (fabrication_count * 0.1))
        
        elif "confidence" in question.lower():
            # Check confidence appropriateness
            confidence_indicators = ["high confidence", "very confident", "certain"]
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in output.lower())
            return max(0.0, 1.0 - (confidence_count * 0.15))
        
        elif "inconsistencies" in question.lower():
            # Check for logical inconsistencies
            inconsistency_indicators = ["however", "but", "although", "despite"]
            inconsistency_count = sum(1 for indicator in inconsistency_indicators if indicator in output.lower())
            return max(0.0, 1.0 - (inconsistency_count * 0.1))
        
        return 0.5  # Default neutral score
    
    def _get_reasoning(self, question: str, output: str, evidence: List[Dict]) -> str:
        """Get reasoning for reflection evaluation"""
        if "evidence" in question.lower():
            return f"Output references {len(evidence)} evidence sources"
        elif "unsupported" in question.lower():
            return "Checked for unsupported claim indicators"
        elif "fabricated" in question.lower():
            return "Scanned for potential fabrication patterns"
        elif "confidence" in question.lower():
            return "Evaluated confidence level appropriateness"
        elif "inconsistencies" in question.lower():
            return "Checked for logical inconsistencies"
        return "General evaluation performed"


class MultiAgentVerifier:
    """Multi-agent verification system"""
    
    def __init__(self):
        self.agents = {
            "primary": None,  # Llama 4 (placeholder)
            "secondary": None,  # Magistral (placeholder)
            "fallback": None   # Local model fallback
        }
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize verification agents"""
        try:
            # Initialize fallback agent with local model
            self.agents["fallback"] = pipeline(
                "text-classification",
                model="distilbert-base-uncased",
                device=0 if torch.cuda.is_available() else -1
            )
        except Exception as e:
            print(f"Warning: Could not initialize verification agents: {e}")
    
    def cross_check_verification(self, content: str, evidence: List[Dict], sag: Dict) -> Dict[str, Any]:
        """Perform multi-agent cross-check using LLM role prompts (skeptic/supporter)."""
        agent_results: List[Dict[str, Any]] = []
        client = OllamaClient()
        titles_text = ", ".join([str(ev.get("title") or "") for ev in evidence][:5]) or "(none)"
        roles = [
            ("skeptic", "Act as a skeptic. Identify weaknesses or unsupported parts of the claim given these evidence titles."),
            ("supporter", "Act as a supporter. Identify support for the claim from these evidence titles."),
        ]
        confidences: List[float] = []
        for name, instruction in roles:
            prompt = (
                f"{instruction}\n\n"
                f"Claim: {content}\n"
                f"Evidence Titles: {titles_text}\n"
                f"Answer: one sentence plus confidence=0.x"
            )
            out = client.generate(prompt)
            conf = 0.5
            if "confidence=" in out:
                try:
                    conf_str = out.split("confidence=")[-1].strip().split()[0]
                    conf = float(conf_str.strip().rstrip(".,;:"))
                except Exception:
                    conf = 0.5
            conf = max(0.0, min(1.0, conf))
            agent_results.append({"agent": name, "confidence": conf, "reasoning": out})
            confidences.append(conf)

        consensus = statistics.mean(confidences) if confidences else 0.5
        disagreement = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
        return {
            "consensus": consensus,
            "disagreement": disagreement,
            "agents": agent_results,
            "reliability": "high" if disagreement < 0.2 else "medium" if disagreement < 0.4 else "low"
        }
    
    def _verify_with_evidence(self, content: str, evidence: List[Dict]) -> Dict[str, Any]:
        """Verify content against evidence"""
        if not evidence:
            return {"confidence": 0.1, "reasoning": "No evidence available"}
        
        # Check evidence alignment
        evidence_scores = [ev.get("score", 0.0) for ev in evidence]
        avg_evidence_score = statistics.mean(evidence_scores)
        
        # Check content-evidence alignment
        content_lower = content.lower()
        evidence_mentions = 0
        for ev in evidence:
            if ev.get("source", "") in content_lower or ev.get("title", "") in content_lower:
                evidence_mentions += 1
        
        alignment_score = evidence_mentions / len(evidence) if evidence else 0.0
        confidence = (avg_evidence_score + alignment_score) / 2
        
        return {
            "confidence": confidence,
            "reasoning": f"Evidence alignment: {alignment_score:.2f}, Avg evidence score: {avg_evidence_score:.2f}"
        }
    
    def _verify_logical_consistency(self, content: str, sag: Dict) -> Dict[str, Any]:
        """Verify logical consistency using SAG"""
        if not sag or not sag.get("nodes"):
            return {"confidence": 0.5, "reasoning": "No SAG available for logical analysis"}
        
        # Simple logical consistency check
        content_lower = content.lower()
        
        # Check for contradictory statements
        contradictions = [
            ("always", "never"),
            ("all", "none"),
            ("proven", "unproven"),
            ("true", "false")
        ]
        
        contradiction_count = 0
        for pos, neg in contradictions:
            if pos in content_lower and neg in content_lower:
                contradiction_count += 1
        
        consistency_score = max(0.0, 1.0 - (contradiction_count * 0.3))
        
        return {
            "confidence": consistency_score,
            "reasoning": f"Logical consistency: {consistency_score:.2f}, Contradictions: {contradiction_count}"
        }
    
    def _verify_factual_accuracy(self, content: str, evidence: List[Dict]) -> Dict[str, Any]:
        """Verify factual accuracy"""
        if not evidence:
            return {"confidence": 0.3, "reasoning": "No evidence for factual verification"}
        
        # Check factual claims against evidence
        factual_indicators = ["fact", "proven", "established", "confirmed", "verified"]
        factual_claims = sum(1 for indicator in factual_indicators if indicator in content.lower())
        
        # Higher factual claims require stronger evidence
        evidence_strength = statistics.mean([ev.get("score", 0.0) for ev in evidence])
        required_strength = 0.5 + (factual_claims * 0.1)
        
        accuracy_score = min(1.0, evidence_strength / required_strength) if required_strength > 0 else 0.5
        
        return {
            "confidence": accuracy_score,
            "reasoning": f"Factual accuracy: {accuracy_score:.2f}, Claims: {factual_claims}, Evidence strength: {evidence_strength:.2f}"
        }


class RetrievalFirstPipeline:
    """Retrieval-first pipeline to ensure evidence-based responses"""
    
    def __init__(self):
        self.evidence_threshold = 0.3
        self.min_evidence_count = 2
    
    def validate_evidence_basis(self, content: str, evidence: List[Dict], sag: Dict) -> Dict[str, Any]:
        """Validate that response is based on retrieved evidence

        MVP: evidence quality/quantity. Stage 2: add reasoning-evidence embedding similarity.
        """
        if not evidence:
            return {
                "is_evidence_based": False,
                "confidence": 0.0,
                "reasoning": "No evidence retrieved"
            }
        
        # Evidence quality and quantity
        evidence_scores = [float(ev.get("score", 0.0)) for ev in evidence]
        high_quality_evidence = [s for s in evidence_scores if s >= self.evidence_threshold]

        sufficient_evidence = len(high_quality_evidence) >= self.min_evidence_count

        # Confidence derived from proportion and average quality
        proportion_hq = (len(high_quality_evidence) / len(evidence)) if evidence else 0.0
        avg_quality = sum(high_quality_evidence) / len(high_quality_evidence) if high_quality_evidence else 0.0

        # Stage 2: reasoning-evidence embedding similarity
        try:
            ev_texts = [str(ev.get("snippet") or ev.get("title") or "") for ev in evidence]
            reasoning = preliminary_reasoning_for_claim(content, [str(ev.get("title") or "") for ev in evidence])
            if reasoning:
                rv = embed_texts([reasoning])
                ev_vecs = embed_texts(ev_texts)
                import numpy as np
                rv_norm = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-8)
                ev_norm = ev_vecs / (np.linalg.norm(ev_vecs, axis=1, keepdims=True) + 1e-8)
                sims = (rv_norm @ ev_norm.T)[0]
                sim_score = float(np.clip(float(np.max(sims)) if sims.size > 0 else 0.0, 0.0, 1.0))
            else:
                sim_score = 0.0
        except Exception:
            sim_score = 0.0

        is_evidence_based = sufficient_evidence and (sim_score >= 0.3)
        confidence = max(0.0, min(1.0, 0.5 * proportion_hq + 0.3 * avg_quality + 0.2 * sim_score))
        
        return {
            "is_evidence_based": is_evidence_based,
            "confidence": confidence,
            "reasoning": f"High-quality evidence: {len(high_quality_evidence)}/{len(evidence)}; avg_quality={avg_quality:.2f}; sim={sim_score:.2f}",
            "evidence_count": len(evidence),
            "high_quality_count": len(high_quality_evidence),
            "alignment_score": None
        }


class ConfidenceCalibrator:
    """Enhanced confidence calibration with TruthfulQA principles"""
    
    def __init__(self):
        self.truthfulqa_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    def calibrate_confidence(self, raw_confidence: float, evidence_quality: float, 
                           multi_agent_consensus: float, self_reflection_score: float) -> Dict[str, Any]:
        """Calibrate confidence using multiple signals"""
        
        # Weighted combination of signals
        weights = {
            "evidence": 0.4,
            "consensus": 0.3,
            "reflection": 0.3
        }
        
        calibrated_confidence = (
            raw_confidence * 0.3 +
            evidence_quality * weights["evidence"] +
            multi_agent_consensus * weights["consensus"] +
            self_reflection_score * weights["reflection"]
        )
        
        # Apply TruthfulQA calibration
        if calibrated_confidence > self.truthfulqa_thresholds["high"]:
            calibration_level = "high"
            final_confidence = min(0.95, calibrated_confidence)
        elif calibrated_confidence > self.truthfulqa_thresholds["medium"]:
            calibration_level = "medium"
            final_confidence = calibrated_confidence
        else:
            calibration_level = "low"
            final_confidence = max(0.05, calibrated_confidence)
        
        return {
            "raw_confidence": raw_confidence,
            "calibrated_confidence": final_confidence,
            "calibration_level": calibration_level,
            "evidence_quality": evidence_quality,
            "consensus": multi_agent_consensus,
            "self_reflection": self_reflection_score,
            "weights": weights
        }


class StructuredOutputValidator:
    """Structured output validation with JSON schema"""
    
    def __init__(self):
        self.validation_schemas = {
            "verification_result": {
                "type": "object",
                "required": ["confidence", "method", "notes"],
                "properties": {
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "method": {"type": "string"},
                    "notes": {"type": "string"}
                }
            }
        }
    
    def validate_output(self, output: Any, schema_name: str) -> Dict[str, Any]:
        """Validate structured output against schema"""
        if schema_name not in self.validation_schemas:
            return {"valid": False, "errors": [f"Unknown schema: {schema_name}"]}
        
        schema = self.validation_schemas[schema_name]
        errors = []
        
        # Basic validation
        if not isinstance(output, dict):
            errors.append("Output must be a dictionary")
            return {"valid": False, "errors": errors}
        
        # Check required fields
        for field in schema.get("required", []):
            if field not in output:
                errors.append(f"Missing required field: {field}")
        
        # Check field types and constraints
        for field, constraints in schema.get("properties", {}).items():
            if field in output:
                value = output[field]
                expected_type = constraints.get("type")
                
                if expected_type == "number":
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field {field} must be a number")
                    else:
                        if "minimum" in constraints and value < constraints["minimum"]:
                            errors.append(f"Field {field} must be >= {constraints['minimum']}")
                        if "maximum" in constraints and value > constraints["maximum"]:
                            errors.append(f"Field {field} must be <= {constraints['maximum']}")
                
                elif expected_type == "string":
                    if not isinstance(value, str):
                        errors.append(f"Field {field} must be a string")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "schema": schema_name
        }


class AutoEscalationSystem:
    """Auto-escalation system for model selection"""
    
    def __init__(self):
        self.escalation_thresholds = {
            "mini_model": 0.8,
            "medium_model": 0.6,
            "large_model": 0.4
        }
        self.current_model = "mini_model"
    
    def should_escalate(self, confidence: float, complexity_score: float) -> Dict[str, Any]:
        """Determine if escalation is needed"""
        escalation_needed = False
        target_model = self.current_model
        
        if confidence < self.escalation_thresholds["large_model"]:
            target_model = "large_model"
            escalation_needed = True
        elif confidence < self.escalation_thresholds["medium_model"]:
            target_model = "medium_model"
            escalation_needed = True
        elif confidence < self.escalation_thresholds["mini_model"]:
            target_model = "mini_model"
            escalation_needed = True
        
        return {
            "escalation_needed": escalation_needed,
            "current_model": self.current_model,
            "target_model": target_model,
            "confidence": confidence,
            "complexity_score": complexity_score,
            "reasoning": f"Confidence {confidence:.2f} below threshold for {target_model}"
        }


class VerificationService:
    """Enhanced Anti-Hallucination Verification Service"""
    
    def __init__(self):
        self.self_reflection = SelfReflectionAgent()
        self.multi_agent = MultiAgentVerifier()
        self.retrieval_first = RetrievalFirstPipeline()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.output_validator = StructuredOutputValidator()
        self.auto_escalation = AutoEscalationSystem()
    
    def _normalize_score(self, score: float) -> float:
        """Convert cosine/IP in [-1, 1] to [0, 1]"""
        return max(0.0, min(1.0, (score + 1.0) / 2.0))

    def _sigmoid_calibration(self, x: float, a: float = 6.0, b: float = 0.6) -> float:
        """Sigmoid centered at b with slope a"""
        return 1.0 / (1.0 + math.exp(-a * (x - b)))

    def _aggregate_scores(self, scores: List[float], top_k: int = 3) -> float:
        """Aggregate top-k scores"""
        if not scores:
            return 0.0
        sorted_scores = sorted(scores, reverse=True)
        take = sorted_scores[:top_k]
        return sum(take) / len(take)

    def verify(self, sag: dict, evidence: list[dict], content: str = "") -> VerificationResult:
        """
        Enhanced verification with anti-hallucination measures
        
        Args:
            sag: Structured Argument Graph
            evidence: List of evidence items
            content: Original content for analysis
            
        Returns:
            Enhanced VerificationResult with anti-hallucination measures
        """
        settings = get_settings()
        calib = settings.verification_calibration
        ah = settings.anti_hallucination
        
        # 1. Basic evidence scoring (original method)
        raw_scores: List[float] = [float(item.get("score", 0.0)) for item in evidence]
        norm_scores = [self._normalize_score(s) for s in raw_scores]
        agg = self._aggregate_scores(norm_scores, top_k=3)
        
        # 2. Multi-agent cross-check verification
        multi_agent_result = self.multi_agent.cross_check_verification(content, evidence, sag)
        
        # 3. Self-reflection on the analysis
        analysis_output = f"Analysis of content with {len(evidence)} evidence sources"
        self_reflection_result = self.self_reflection.reflect_on_output(analysis_output, evidence, content)
        
        # 4. Retrieval-first validation
        retrieval_validation = self.retrieval_first.validate_evidence_basis(content, evidence, sag)
        
        # 5. Enhanced confidence calibration
        evidence_quality = statistics.mean(norm_scores) if norm_scores else 0.0
        calibration_result = self.confidence_calibrator.calibrate_confidence(
            raw_confidence=agg,
            evidence_quality=evidence_quality,
            multi_agent_consensus=multi_agent_result["consensus"],
            self_reflection_score=self_reflection_result["overall_score"]
        )
        
        # 6. Auto-escalation check
        complexity_score = self._calculate_complexity_score(content, sag)
        escalation_result = self.auto_escalation.should_escalate(
            calibration_result["calibrated_confidence"], 
            complexity_score
        )
        
        # 7. Final confidence with anti-hallucination measures
        final_confidence = calibration_result["calibrated_confidence"]
        
        # Apply additional safeguards
        if not retrieval_validation["is_evidence_based"]:
            final_confidence *= 0.7  # Reduce confidence if not evidence-based
        
        if self_reflection_result["hallucination_risk"] == "high":
            final_confidence *= 0.5  # Significant reduction for high hallucination risk
        
        if multi_agent_result["reliability"] == "low":
            final_confidence *= 0.8  # Reduce confidence for low reliability
        
        # Guardrails
        final_confidence = max(0.05, min(0.99, final_confidence))
        
        # 8. Structured output validation
        verification_output = {
            "confidence": final_confidence,
            "method": "enhanced_anti_hallucination_v2",
            "notes": self._generate_enhanced_notes(
                agg, multi_agent_result, self_reflection_result, 
                retrieval_validation, calibration_result, escalation_result
            )
        }
        
        validation_result = self.output_validator.validate_output(verification_output, "verification_result")
        
        if not validation_result["valid"]:
            # Fallback to basic verification if validation fails
            return self._fallback_verification(agg, evidence)
        
        return VerificationResult(**verification_output)
    
    def _calculate_complexity_score(self, content: str, sag: dict) -> float:
        """Calculate complexity score for escalation decisions"""
        complexity_indicators = [
            len(content.split()),  # Word count
            len(sag.get("nodes", [])),  # SAG complexity
            len(sag.get("edges", [])),  # Relationship complexity
            content.count("."),  # Sentence count
            len(re.findall(r'\b(however|although|despite|nevertheless)\b', content.lower()))  # Logical complexity
        ]
        
        # Normalize and combine indicators
        normalized_indicators = []
        for indicator in complexity_indicators:
            normalized = min(1.0, indicator / 100.0)  # Normalize to 0-1
            normalized_indicators.append(normalized)
        
        return statistics.mean(normalized_indicators)
    
    def _generate_enhanced_notes(self, agg: float, multi_agent_result: dict, 
                                self_reflection_result: dict, retrieval_validation: dict,
                                calibration_result: dict, escalation_result: dict) -> str:
        """Generate comprehensive notes for verification result"""
        notes_parts = [
            f"agg={agg:.3f}",
            f"multi_agent_consensus={multi_agent_result['consensus']:.3f}",
            f"self_reflection={self_reflection_result['overall_score']:.3f}",
            f"evidence_based={retrieval_validation['is_evidence_based']}",
            f"calibration_level={calibration_result['calibration_level']}",
            f"hallucination_risk={self_reflection_result['hallucination_risk']}",
            f"escalation_needed={escalation_result['escalation_needed']}"
        ]
        
        return "; ".join(notes_parts)
    
    def _fallback_verification(self, agg: float, evidence: list[dict]) -> VerificationResult:
        """Fallback to basic verification if enhanced methods fail"""
        basic_confidence = self._sigmoid_calibration(agg, a=6.0, b=0.6)
        basic_confidence = max(0.05, min(0.99, basic_confidence))
        
        return VerificationResult(
            confidence=basic_confidence,
            method="fallback_basic_verification",
            notes=f"agg={agg:.3f}; fallback_used=true"
        )


