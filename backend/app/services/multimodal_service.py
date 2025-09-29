from __future__ import annotations

"""
Multimodal service skeleton for deepfake/media authenticity checks.
This is a placeholder with clean interfaces to integrate local models later.
"""

from typing import Any, Dict, Optional


class MediaAnalysisResult(dict):
    """Lightweight dict-based result for media analysis."""
    pass


class MultimodalService:
    def __init__(self) -> None:
        self.enabled = True

    def analyze_image(self, image_bytes: bytes, metadata: Optional[Dict[str, Any]] = None) -> MediaAnalysisResult:
        if not self.enabled:
            return MediaAnalysisResult({"supported": False, "reason": "disabled"})
        # Placeholder: return neutral analysis
        return MediaAnalysisResult({
            "supported": True,
            "modality": "image",
            "is_deepfake": False,
            "confidence": 0.5,
            "signals": {},
            "metadata": metadata or {},
        })

    def analyze_audio(self, audio_bytes: bytes, metadata: Optional[Dict[str, Any]] = None) -> MediaAnalysisResult:
        if not self.enabled:
            return MediaAnalysisResult({"supported": False, "reason": "disabled"})
        return MediaAnalysisResult({
            "supported": True,
            "modality": "audio",
            "is_deepfake": False,
            "confidence": 0.5,
            "signals": {},
            "metadata": metadata or {},
        })

    def analyze_video(self, video_bytes: bytes, metadata: Optional[Dict[str, Any]] = None) -> MediaAnalysisResult:
        if not self.enabled:
            return MediaAnalysisResult({"supported": False, "reason": "disabled"})
        return MediaAnalysisResult({
            "supported": True,
            "modality": "video",
            "is_deepfake": False,
            "confidence": 0.5,
            "signals": {},
            "metadata": metadata or {},
        })


