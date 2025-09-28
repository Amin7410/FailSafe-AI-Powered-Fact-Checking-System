# FILE: backend/app/services/synthesis_service.py

from typing import Dict, Any, List, Optional
from ..models.report import ReportResponse, EvidenceItem, VerificationResult, FallacyItem, AIDetectionResult, MultilingualData
from ..models.claim import ClaimRequest
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class SynthesisService:
    """Service for synthesizing analysis results into final reports"""

    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }

    def summarize(
        self,
        original_input: ClaimRequest,
        sag: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        verification: VerificationResult,
        fallacies: List[FallacyItem],
        multilingual_data: Dict[str, Any],
        ai_detection: AIDetectionResult
    ) -> ReportResponse:
        """
        Synthesize all analysis results into a comprehensive report.
        This method now expects pre-processed Pydantic objects for verification, fallacies, and ai_detection.
        """
        try:
            analysis_id = str(uuid.uuid4())

            # Evidence is still raw dicts, so we process it.
            evidence_items = [EvidenceItem(**item) for item in evidence]

            # Calculate overall confidence based on the final, processed objects.
            overall_confidence = self._calculate_overall_confidence(
                verification, evidence_items, fallacies
            )

            # Determine the final verdict.
            verdict = self._determine_verdict(verification.confidence, overall_confidence)

            # Process multilingual data into a Pydantic model.
            multilingual_result = MultilingualData(
                detected_language=multilingual_data.get("language_detection", {}).get("language", "en"),
                processing_language=multilingual_data.get("sag_data", {}).get("language", "en"),
                translation_info=multilingual_data.get("translation"),
                cross_lingual_mappings=multilingual_data.get("cross_lingual_analysis", {}).get("mappings", []),
                supported_languages=multilingual_data.get("cross_lingual_analysis", {}).get("supported_languages", [])
            )

            # Create the final report response.
            report = ReportResponse(
                claim_id=analysis_id,
                verdict=verdict,
                confidence=overall_confidence,
                evidence=evidence_items,
                verification=verification,
                fallacies=fallacies,
                ai_detection=ai_detection,
                multilingual=multilingual_result,
                sag=sag,
                provenance={
                    "timestamp": datetime.utcnow().isoformat(),
                    "input_text": original_input.text,
                    "input_url": str(original_input.url) if original_input.url else None,
                    "processing_time_ms": self._calculate_processing_time(),
                    "language": original_input.language,
                    "user_metadata": original_input.metadata,
                    "analysis_version": "1.0.1" # Version bump
                }
            )

            logger.info(f"Generated comprehensive report for analysis {analysis_id}")
            return report

        except Exception as e:
            logger.error(f"Error synthesizing report: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to synthesize report: {e}")

    def _calculate_overall_confidence(
        self,
        verification: VerificationResult,
        evidence: List[EvidenceItem],
        fallacies: List[FallacyItem]
    ) -> float:
        """Calculate overall confidence score"""
        base_confidence = verification.confidence

        if evidence:
            # Evidence quality now uses score directly from the Pydantic model
            avg_evidence_quality = sum(e.score or 0.0 for e in evidence) / len(evidence)
            evidence_factor = min(1.0, avg_evidence_quality)
        else:
            evidence_factor = 0.5

        fallacy_penalty = 0.0
        if fallacies:
            # Assuming FallacyItem has a confidence attribute
            high_confidence_fallacies = [f for f in fallacies if hasattr(f, 'confidence') and f.confidence > 0.7]
            fallacy_penalty = min(0.3, len(high_confidence_fallacies) * 0.1)

        final_confidence = (base_confidence * evidence_factor) - fallacy_penalty
        return max(0.0, min(1.0, final_confidence))

    def _determine_verdict(self, verification_confidence: float, overall_confidence: float) -> str:
        """Determine final verdict based on verification and confidence"""
        if verification_confidence < 0.1:
            return "Unverifiable"

        if overall_confidence >= self.confidence_thresholds["high"]:
            return "True"
        elif overall_confidence >= self.confidence_thresholds["medium"]:
            return "Mixed"
        else:
            return "False"

    def _calculate_processing_time(self) -> int:
        """Calculate processing time (placeholder)"""
        return 1500