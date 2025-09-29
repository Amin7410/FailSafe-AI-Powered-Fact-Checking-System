from __future__ import annotations

"""
Orchestrator: iterate analysis until confidence >= threshold or max rounds.
Integrates ingestion, SAG, retrieval, verification, and optional refinement.
"""

from typing import Any, Dict, List, Optional

from .ingestion_service import IngestionService
from .sag_generator import SAGGenerator
from .retrieval_service import RetrievalService
from .verification_service import VerificationService
from .synthesis_service import SynthesisService
from ..models.claim import ClaimRequest
from ..models.report import ReportResponse


class Orchestrator:
    def __init__(self, confidence_threshold: float = 0.75, max_rounds: int = 3) -> None:
        self.confidence_threshold = confidence_threshold
        self.max_rounds = max_rounds

    def analyze_until_confident(self, payload: ClaimRequest) -> ReportResponse:
        ingestion = IngestionService()
        content = ingestion.process_input(payload)

        sag_generator = SAGGenerator()
        retrieval = RetrievalService()
        verifier = VerificationService()
        synthesizer = SynthesisService()

        last_report: Optional[ReportResponse] = None
        for _ in range(max(1, self.max_rounds)):
            # Generate/refresh SAG and retrieve evidence
            sag = sag_generator.generate(content, payload.language or "en")
            evidence = retrieval.retrieve(sag, payload.language or "en")

            # Verify and synthesize
            verification = verifier.verify(sag, evidence, content)
            report = synthesizer.summarize(
                original_input=payload,
                sag=sag,
                evidence=evidence,
                verification=verification,
                fallacies=[],
                multilingual_data={"language_detection": {"language": payload.language or "en"}, "sag_data": {"language": payload.language or "en"}},
                ai_detection=None,  # Leave as None in loop; upstream pipeline fills in normally
            )
            last_report = report
            if report.confidence >= self.confidence_threshold:
                break

        return last_report  # type: ignore[return-value]


