from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Any


class EvidenceItem(BaseModel):
    source: HttpUrl | str
    title: str | None = None
    snippet: str | None = None
    score: float | None = None
    provenance_timestamp: datetime | None = None


class VerificationResult(BaseModel):
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: str = Field(..., description="verification strategy used")
    notes: str | None = None


class FallacyItem(BaseModel):
    type: str
    span: str | None = None
    explanation: str | None = None


class AIDetectionResult(BaseModel):
    is_ai_generated: bool = Field(..., description="Whether content is detected as AI-generated")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in AI detection")
    method: str = Field(..., description="Detection method used")
    scores: dict[str, float] = Field(default_factory=dict, description="Individual detection scores")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed detection results")


class MultilingualData(BaseModel):
    detected_language: str = Field(..., description="Automatically detected language")
    processing_language: str = Field(..., description="Language used for processing")
    translation_info: dict[str, Any] | None = Field(None, description="Translation details if applicable")
    cross_lingual_mappings: list[dict[str, Any]] = Field(default_factory=list, description="Cross-lingual concept mappings")
    supported_languages: list[str] = Field(default_factory=list, description="List of supported languages")


class ReportResponse(BaseModel):
    claim_id: str | None = None
    verdict: str = Field(..., description="true/false/mixed/unverifiable")
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = []
    verification: VerificationResult
    fallacies: list[FallacyItem] = []
    ai_detection: AIDetectionResult | None = None
    multilingual: MultilingualData | None = None
    provenance: dict[str, Any] = {}
    sag: dict[str, Any] = Field(default_factory=dict, description="Structured Argument Graph")



