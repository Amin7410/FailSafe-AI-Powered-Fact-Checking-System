# FILE: backend/app/api/v1/endpoints/analyze.py

from fastapi import APIRouter, HTTPException, Depends, Header
from app.models.claim import ClaimRequest
from app.models.report import ReportResponse, AIDetectionResult # Đảm bảo import AIDetectionResult
from app.services.ingestion_service import IngestionService
from app.services.sag_generator import SAGGenerator
from app.services.retrieval_service import RetrievalService
from app.services.verification_service import VerificationService
from app.services.fallacy_detector import FallacyDetector
from app.services.synthesis_service import SynthesisService
from app.services.graph_service import GraphService
from app.services.ai_detection_service import AIDetectionService
from app.services.multilingual_service import MultilingualService

router = APIRouter(prefix="/analyze")

def _require_api_key(x_api_key: str = Header(None)) -> None:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.api_keys and (x_api_key not in settings.api_keys):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@router.post("", response_model=ReportResponse)
def analyze_claim(payload: ClaimRequest, _: None = Depends(_require_api_key)) -> ReportResponse:
    try:
        ingestion = IngestionService()
        content = ingestion.process_input(payload)

        multilingual_service = MultilingualService()
        multilingual_result = multilingual_service.process_multilingual_content(
            content, payload.language
        )
        processing_language = payload.language or multilingual_result["language_detection"]["language"]

        ai_detector = AIDetectionService()
        ai_detection_dict = ai_detector.detect_ai_generated(content, payload.metadata)
        ai_detection = AIDetectionResult(**ai_detection_dict)

        sag_generator = SAGGenerator()
        sag = sag_generator.generate(content, processing_language)
        
        sag.update(multilingual_result["sag_data"])

        retrieval = RetrievalService()
        evidence = retrieval.retrieve(sag, processing_language)

        verifier = VerificationService()
        verification = verifier.verify(sag, evidence, content)

        # Đổi tên biến để tránh nhầm lẫn
        fallacy_detector = FallacyDetector()
        detected_fallacies = fallacy_detector.detect(content)

        synthesis = SynthesisService()
        report = synthesis.summarize(
            original_input=payload, 
            sag=sag, 
            evidence=evidence, 
            verification=verification, 
            fallacies=detected_fallacies, # Sử dụng biến đã đổi tên
            multilingual_data=multilingual_result,
            ai_detection=ai_detection
        )
        
        # Các đoạn code bị comment out có thể để nguyên hoặc xóa đi
        
        return report
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))