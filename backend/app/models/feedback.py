"""
Feedback Models

Pydantic models for user feedback and collaboration.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """Types of user feedback"""
    RATING = "rating"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    analysis_id: str = Field(..., description="ID of the analysis being rated")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    score: Optional[int] = Field(None, ge=1, le=5, description="Rating score (1-5)")
    comment: Optional[str] = Field(None, max_length=1000, description="Feedback comment")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    feedback_id: str = Field(..., description="Unique feedback ID")
    analysis_id: str = Field(..., description="Analysis ID")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    score: Optional[int] = Field(None, description="Rating score")
    comment: Optional[str] = Field(None, description="Feedback comment")
    timestamp: datetime = Field(..., description="When feedback was submitted")
    user_id: Optional[str] = Field(None, description="User ID")
    status: str = Field(..., description="Processing status")


class OverrideRequest(BaseModel):
    """Request model for user overrides"""
    analysis_id: str = Field(..., description="ID of the analysis")
    override_type: str = Field(..., description="Type of override")
    original_value: Any = Field(..., description="Original value")
    new_value: Any = Field(..., description="New value")
    reason: str = Field(..., max_length=500, description="Reason for override")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OverrideResponse(BaseModel):
    """Response model for override submission"""
    override_id: str = Field(..., description="Unique override ID")
    analysis_id: str = Field(..., description="Analysis ID")
    override_type: str = Field(..., description="Type of override")
    original_value: Any = Field(..., description="Original value")
    new_value: Any = Field(..., description="New value")
    reason: str = Field(..., description="Reason for override")
    timestamp: datetime = Field(..., description="When override was submitted")
    user_id: Optional[str] = Field(None, description="User ID")
    status: str = Field(..., description="Processing status")


class CollaborationSession(BaseModel):
    """Model for collaboration session"""
    session_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(..., description="User ID")
    analysis_id: str = Field(..., description="Analysis ID")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    feedback_count: int = Field(0, description="Number of feedback items")
    override_count: int = Field(0, description="Number of overrides")
    status: str = Field("active", description="Session status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class FeedbackSummary(BaseModel):
    """Summary of feedback for an analysis"""
    analysis_id: str = Field(..., description="Analysis ID")
    total_feedback: int = Field(..., description="Total number of feedback items")
    average_score: Optional[float] = Field(None, description="Average rating score")
    feedback_types: Dict[str, int] = Field(..., description="Count by feedback type")
    recent_feedback: list = Field(..., description="Recent feedback items")
    last_updated: datetime = Field(..., description="Last update time")


class OverrideSummary(BaseModel):
    """Summary of overrides for an analysis"""
    analysis_id: str = Field(..., description="Analysis ID")
    total_overrides: int = Field(..., description="Total number of overrides")
    override_types: Dict[str, int] = Field(..., description="Count by override type")
    recent_overrides: list = Field(..., description="Recent override items")
    last_updated: datetime = Field(..., description="Last update time")






