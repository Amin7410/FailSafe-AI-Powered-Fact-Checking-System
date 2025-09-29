from __future__ import annotations

from typing import Any, List

from app.services.verification_service import VerificationService
from app.services.synthesis_service import SynthesisService
from app.models.claim import ClaimRequest
from app.models.report import VerificationResult


def test_verification_basic_no_evidence() -> None:
    verifier = VerificationService()
    sag: dict[str, Any] = {"nodes": [], "edges": [], "analysis_id": "t1", "language": "en", "raw": "simple claim"}
    evidence: list[dict] = []
    content = "This is a simple test claim."

    result: VerificationResult = verifier.verify(sag, evidence, content)

    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.method, str) and result.method
    assert result.notes is None or isinstance(result.notes, str)


def test_synthesis_verdict_casing_and_notes() -> None:
    synthesizer = SynthesisService()

    claim = ClaimRequest(text="Vaccines are safe.", url=None, language="en", metadata=None)
    sag: dict[str, Any] = {
        "analysis_id": "t2",
        "language": "en",
        "nodes": [{"id": "c1", "type": "claim", "label": "Vaccines are safe"}],
        "edges": []
    }
    evidence: List[dict] = [
        {"id": "doc1", "source": "https://example.org/study", "title": "Study", "snippet": "...", "score": 0.8},
    ]

    # Minimal verification obj
    verification = VerificationResult(confidence=0.7, method="unit_test", notes=None)
    fallacies: list[Any] = []
    multilingual_data: dict[str, Any] = {"language_detection": {"language": "en"}, "sag_data": {"language": "en"}}
    ai_detection = None  # type: ignore

    report = synthesizer.summarize(
        original_input=claim,
        sag=sag,
        evidence=evidence,
        verification=verification,
        fallacies=fallacies,
        multilingual_data=multilingual_data,
        ai_detection=ai_detection,
    )

    assert report.verdict in {"true", "mixed", "false", "unverifiable"}
    assert 0.0 <= report.confidence <= 1.0
    # Notes may include appended reasoning; must remain a string
    assert isinstance(report.verification.notes, (str, type(None)))


