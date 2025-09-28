"""
Human-AI Collaboration API Endpoints

Provides endpoints for human-AI collaboration including feedback,
overrides, and guidance mechanisms.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.collaboration_service import (
    collaboration_service,
    CollaborationType,
    FeedbackType,
    OverrideType,
    UserFeedback,
    UserOverride,
    CollaborationSession
)
from app.models.report import ReportResponse

router = APIRouter(prefix="/collaboration")


@router.post("/sessions", response_model=Dict[str, str])
def create_collaboration_session(
    user_id: str = Body(..., description="User ID"),
    analysis_id: str = Body(..., description="Analysis ID"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Session metadata")
) -> Dict[str, str]:
    """Create a new collaboration session"""
    try:
        session = collaboration_service.create_collaboration_session(
            user_id=user_id,
            analysis_id=analysis_id,
            metadata=metadata
        )
        return {
            "session_id": session.id,
            "message": "Collaboration session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
def get_collaboration_session(
    session_id: str = Path(..., description="Session ID")
) -> Dict[str, Any]:
    """Get collaboration session details"""
    try:
        session = collaboration_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=Dict[str, str])
def submit_feedback(
    user_id: str = Body(..., description="User ID"),
    session_id: str = Body(..., description="Session ID"),
    analysis_id: str = Body(..., description="Analysis ID"),
    feedback_type: FeedbackType = Body(..., description="Type of feedback"),
    rating: int = Body(..., ge=1, le=5, description="Rating from 1 to 5"),
    comment: Optional[str] = Body(None, description="Optional comment"),
    specific_element: Optional[str] = Body(None, description="Specific element being rated"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, str]:
    """Submit user feedback"""
    try:
        feedback = collaboration_service.submit_feedback(
            user_id=user_id,
            session_id=session_id,
            analysis_id=analysis_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            specific_element=specific_element,
            metadata=metadata
        )
        return {
            "feedback_id": feedback.id,
            "message": "Feedback submitted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/overrides", response_model=Dict[str, str])
def submit_override(
    user_id: str = Body(..., description="User ID"),
    session_id: str = Body(..., description="Session ID"),
    analysis_id: str = Body(..., description="Analysis ID"),
    override_type: OverrideType = Body(..., description="Type of override"),
    original_value: Any = Body(..., description="Original value"),
    new_value: Any = Body(..., description="New value"),
    reason: str = Body(..., description="Reason for override"),
    confidence: float = Body(..., ge=0.0, le=1.0, description="User confidence in override"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, str]:
    """Submit user override"""
    try:
        override = collaboration_service.submit_override(
            user_id=user_id,
            session_id=session_id,
            analysis_id=analysis_id,
            override_type=override_type,
            original_value=original_value,
            new_value=new_value,
            reason=reason,
            confidence=confidence,
            metadata=metadata
        )
        return {
            "override_id": override.id,
            "message": "Override submitted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/feedback", response_model=List[Dict[str, Any]])
def get_session_feedback(
    session_id: str = Path(..., description="Session ID")
) -> List[Dict[str, Any]]:
    """Get all feedback for a session"""
    try:
        feedback = collaboration_service.get_session_feedback(session_id)
        return [f.to_dict() for f in feedback]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/overrides", response_model=List[Dict[str, Any]])
def get_session_overrides(
    session_id: str = Path(..., description="Session ID")
) -> List[Dict[str, Any]]:
    """Get all overrides for a session"""
    try:
        overrides = collaboration_service.get_session_overrides(session_id)
        return [o.to_dict() for o in overrides]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}", response_model=Dict[str, Any])
def get_analysis_collaboration(
    analysis_id: str = Path(..., description="Analysis ID")
) -> Dict[str, Any]:
    """Get collaboration data for an analysis"""
    try:
        return collaboration_service.get_analysis_collaboration(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/sessions", response_model=List[Dict[str, Any]])
def get_user_sessions(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
) -> List[Dict[str, Any]]:
    """Get all sessions for a user"""
    try:
        sessions = collaboration_service.get_user_sessions(user_id)
        return [s.to_dict() for s in sessions[offset:offset + limit]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/insights", response_model=Dict[str, Any])
def get_user_insights(
    user_id: str = Path(..., description="User ID")
) -> Dict[str, Any]:
    """Get collaboration insights for a user"""
    try:
        return collaboration_service.get_collaboration_insights(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guidance", response_model=Dict[str, Any])
def apply_user_guidance(
    analysis_id: str = Body(..., description="Analysis ID"),
    guidance_type: str = Body(..., description="Type of guidance"),
    guidance_data: Dict[str, Any] = Body(..., description="Guidance data"),
    user_id: str = Body(..., description="User ID")
) -> Dict[str, Any]:
    """Apply user guidance to analysis"""
    try:
        return collaboration_service.apply_user_guidance(
            analysis_id=analysis_id,
            guidance_type=guidance_type,
            guidance_data=guidance_data,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=List[Dict[str, Any]])
def get_collaboration_recommendations(
    analysis_id: str = Query(..., description="Analysis ID"),
    user_id: str = Query(..., description="User ID")
) -> List[Dict[str, Any]]:
    """Get collaboration recommendations for user"""
    try:
        return collaboration_service.get_collaboration_recommendations(
            analysis_id=analysis_id,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/feedback", response_model=List[str])
def get_feedback_types() -> List[str]:
    """Get available feedback types"""
    return [ft.value for ft in FeedbackType]


@router.get("/types/overrides", response_model=List[str])
def get_override_types() -> List[str]:
    """Get available override types"""
    return [ot.value for ot in OverrideType]


@router.get("/types/collaboration", response_model=List[str])
def get_collaboration_types() -> List[str]:
    """Get available collaboration types"""
    return [ct.value for ct in CollaborationType]


@router.get("/health", response_model=Dict[str, Any])
def collaboration_health_check() -> Dict[str, Any]:
    """Health check for collaboration system"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_sessions": len(collaboration_service.session_store),
            "total_feedback": len(collaboration_service.feedback_store),
            "total_overrides": len(collaboration_service.override_store)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

