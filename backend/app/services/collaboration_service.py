"""
Human-AI Collaboration Service

Implements the Dual-Route Persuasion Framework for human-AI collaboration,
allowing users to provide feedback, override AI decisions, and guide the analysis.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.config import get_settings
from .provenance_service import provenance_tracker, ProvenanceType, SourceType


class CollaborationType(Enum):
    """Types of human collaboration"""
    FEEDBACK = "feedback"
    OVERRIDE = "override"
    GUIDANCE = "guidance"
    CORRECTION = "correction"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    REFINEMENT = "refinement"


class FeedbackType(Enum):
    """Types of user feedback"""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    BIAS = "bias"
    CONFIDENCE = "confidence"
    SOURCE_QUALITY = "source_quality"
    LOGICAL_FLOW = "logical_flow"


class OverrideType(Enum):
    """Types of user overrides"""
    VERDICT = "verdict"
    CONFIDENCE = "confidence"
    EVIDENCE = "evidence"
    FALLACY = "fallacy"
    SOURCE = "source"
    ANALYSIS = "analysis"
    CONCLUSION = "conclusion"


@dataclass
class UserFeedback:
    """User feedback on analysis results"""
    id: str
    user_id: str
    session_id: str
    analysis_id: str
    feedback_type: FeedbackType
    rating: int  # 1-5 scale
    comment: Optional[str] = None
    specific_element: Optional[str] = None  # ID of specific element being rated
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['feedback_type'] = self.feedback_type.value
        return data


@dataclass
class UserOverride:
    """User override of AI decision"""
    id: str
    user_id: str
    session_id: str
    analysis_id: str
    override_type: OverrideType
    original_value: Any
    new_value: Any
    reason: str
    confidence: float  # User's confidence in the override
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['override_type'] = self.override_type.value
        return data


@dataclass
class CollaborationSession:
    """Session tracking human-AI collaboration"""
    id: str
    user_id: str
    analysis_id: str
    created_at: datetime
    last_updated: datetime
    feedback_count: int = 0
    override_count: int = 0
    collaboration_score: float = 0.0
    status: str = "active"  # active, completed, abandoned
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data


class HumanAICollaborationService:
    """Service for managing human-AI collaboration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.feedback_store: Dict[str, UserFeedback] = {}
        self.override_store: Dict[str, UserOverride] = {}
        self.session_store: Dict[str, CollaborationSession] = {}
    
    def create_collaboration_session(
        self,
        user_id: str,
        analysis_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        session = CollaborationSession(
            id=session_id,
            user_id=user_id,
            analysis_id=analysis_id,
            created_at=now,
            last_updated=now,
            metadata=metadata or {}
        )
        
        self.session_store[session_id] = session
        
        # Track in provenance
        provenance_tracker.track_processing(
            operation="collaboration_session_created",
            source_id=session_id,
            source_type=SourceType.USER_INPUT,
            parameters={
                "user_id": user_id,
                "analysis_id": analysis_id,
                "session_type": "human_ai_collaboration"
            }
        )
        
        return session
    
    def submit_feedback(
        self,
        user_id: str,
        session_id: str,
        analysis_id: str,
        feedback_type: FeedbackType,
        rating: int,
        comment: Optional[str] = None,
        specific_element: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """Submit user feedback"""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        feedback_id = str(uuid.uuid4())
        
        feedback = UserFeedback(
            id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            analysis_id=analysis_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            specific_element=specific_element,
            metadata=metadata or {}
        )
        
        self.feedback_store[feedback_id] = feedback
        
        # Update session
        if session_id in self.session_store:
            session = self.session_store[session_id]
            session.feedback_count += 1
            session.last_updated = datetime.now(timezone.utc)
            self._update_collaboration_score(session)
        
        # Track in provenance
        provenance_tracker.track_user_feedback(
            feedback_id=feedback_id,
            feedback_type=feedback_type.value,
            user_id=user_id,
            metadata={
                "rating": rating,
                "comment": comment,
                "specific_element": specific_element,
                "analysis_id": analysis_id
            }
        )
        
        return feedback
    
    def submit_override(
        self,
        user_id: str,
        session_id: str,
        analysis_id: str,
        override_type: OverrideType,
        original_value: Any,
        new_value: Any,
        reason: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserOverride:
        """Submit user override"""
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        override_id = str(uuid.uuid4())
        
        override = UserOverride(
            id=override_id,
            user_id=user_id,
            session_id=session_id,
            analysis_id=analysis_id,
            override_type=override_type,
            original_value=original_value,
            new_value=new_value,
            reason=reason,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        self.override_store[override_id] = override
        
        # Update session
        if session_id in self.session_store:
            session = self.session_store[session_id]
            session.override_count += 1
            session.last_updated = datetime.now(timezone.utc)
            self._update_collaboration_score(session)
        
        # Track in provenance
        provenance_tracker.track_processing(
            operation=f"user_override_{override_type.value}",
            source_id=override_id,
            source_type=SourceType.USER_INPUT,
            parameters={
                "user_id": user_id,
                "override_type": override_type.value,
                "original_value": str(original_value),
                "new_value": str(new_value),
                "reason": reason,
                "confidence": confidence,
                "analysis_id": analysis_id
            }
        )
        
        return override
    
    def get_session_feedback(self, session_id: str) -> List[UserFeedback]:
        """Get all feedback for a session"""
        return [f for f in self.feedback_store.values() if f.session_id == session_id]
    
    def get_session_overrides(self, session_id: str) -> List[UserOverride]:
        """Get all overrides for a session"""
        return [o for o in self.override_store.values() if o.session_id == session_id]
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session by ID"""
        return self.session_store.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[CollaborationSession]:
        """Get all sessions for a user"""
        return [s for s in self.session_store.values() if s.user_id == user_id]
    
    def get_analysis_collaboration(self, analysis_id: str) -> Dict[str, Any]:
        """Get collaboration data for an analysis"""
        sessions = [s for s in self.session_store.values() if s.analysis_id == analysis_id]
        feedback = [f for f in self.feedback_store.values() if f.analysis_id == analysis_id]
        overrides = [o for o in self.override_store.values() if o.analysis_id == analysis_id]
        
        return {
            "analysis_id": analysis_id,
            "sessions": [s.to_dict() for s in sessions],
            "feedback": [f.to_dict() for f in feedback],
            "overrides": [o.to_dict() for o in overrides],
            "total_feedback": len(feedback),
            "total_overrides": len(overrides),
            "collaboration_score": sum(s.collaboration_score for s in sessions) / len(sessions) if sessions else 0.0
        }
    
    def get_collaboration_insights(self, user_id: str) -> Dict[str, Any]:
        """Get collaboration insights for a user"""
        user_sessions = self.get_user_sessions(user_id)
        user_feedback = [f for f in self.feedback_store.values() if f.user_id == user_id]
        user_overrides = [o for o in self.override_store.values() if o.user_id == user_id]
        
        # Calculate insights
        avg_rating = sum(f.rating for f in user_feedback) / len(user_feedback) if user_feedback else 0
        feedback_by_type = {}
        for f in user_feedback:
            type_name = f.feedback_type.value
            if type_name not in feedback_by_type:
                feedback_by_type[type_name] = []
            feedback_by_type[type_name].append(f.rating)
        
        override_by_type = {}
        for o in user_overrides:
            type_name = o.override_type.value
            if type_name not in override_by_type:
                override_by_type[type_name] = 0
            override_by_type[type_name] += 1
        
        return {
            "user_id": user_id,
            "total_sessions": len(user_sessions),
            "total_feedback": len(user_feedback),
            "total_overrides": len(user_overrides),
            "average_rating": avg_rating,
            "feedback_by_type": {k: sum(v)/len(v) for k, v in feedback_by_type.items()},
            "override_frequency": override_by_type,
            "collaboration_engagement": self._calculate_engagement_score(user_sessions, user_feedback, user_overrides)
        }
    
    def apply_user_guidance(
        self,
        analysis_id: str,
        guidance_type: str,
        guidance_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Apply user guidance to analysis"""
        guidance_id = str(uuid.uuid4())
        
        # Track guidance application
        provenance_tracker.track_processing(
            operation=f"user_guidance_{guidance_type}",
            source_id=guidance_id,
            source_type=SourceType.USER_INPUT,
            parameters={
                "user_id": user_id,
                "guidance_type": guidance_type,
                "guidance_data": guidance_data,
                "analysis_id": analysis_id
            }
        )
        
        return {
            "guidance_id": guidance_id,
            "applied": True,
            "guidance_type": guidance_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_collaboration_recommendations(
        self,
        analysis_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get collaboration recommendations for user"""
        recommendations = []
        
        # Get analysis data (this would come from the analysis service)
        # For now, we'll provide generic recommendations
        
        recommendations.append({
            "type": "feedback_prompt",
            "title": "Rate the analysis accuracy",
            "description": "Help improve the system by rating how accurate you found this analysis",
            "priority": "high",
            "action": "submit_feedback",
            "parameters": {
                "feedback_type": "accuracy",
                "specific_element": "verdict"
            }
        })
        
        recommendations.append({
            "type": "override_suggestion",
            "title": "Review evidence quality",
            "description": "Check if the evidence sources are relevant and credible",
            "priority": "medium",
            "action": "review_evidence",
            "parameters": {
                "override_type": "evidence",
                "focus_area": "source_quality"
            }
        })
        
        recommendations.append({
            "type": "guidance_offer",
            "title": "Provide domain expertise",
            "description": "Share your expertise to improve the analysis",
            "priority": "low",
            "action": "provide_guidance",
            "parameters": {
                "guidance_type": "domain_expertise",
                "fields": ["context", "additional_sources", "methodology"]
            }
        })
        
        return recommendations
    
    def _update_collaboration_score(self, session: CollaborationSession):
        """Update collaboration score for a session"""
        feedback = self.get_session_feedback(session.session_id)
        overrides = self.get_session_overrides(session.session_id)
        
        # Calculate score based on engagement
        feedback_score = sum(f.rating for f in feedback) / 5.0 if feedback else 0.0
        override_score = min(len(overrides) * 0.1, 1.0)  # Cap at 1.0
        engagement_score = (len(feedback) + len(overrides)) * 0.05  # Engagement factor
        
        session.collaboration_score = min(
            (feedback_score + override_score + engagement_score) / 3.0,
            1.0
        )
    
    def _calculate_engagement_score(
        self,
        sessions: List[CollaborationSession],
        feedback: List[UserFeedback],
        overrides: List[UserOverride]
    ) -> float:
        """Calculate overall engagement score for a user"""
        if not sessions:
            return 0.0
        
        total_sessions = len(sessions)
        avg_feedback_per_session = len(feedback) / total_sessions if total_sessions > 0 else 0
        avg_overrides_per_session = len(overrides) / total_sessions if total_sessions > 0 else 0
        avg_collaboration_score = sum(s.collaboration_score for s in sessions) / total_sessions
        
        # Weighted combination
        engagement = (
            avg_collaboration_score * 0.5 +
            min(avg_feedback_per_session / 3.0, 1.0) * 0.3 +
            min(avg_overrides_per_session / 2.0, 1.0) * 0.2
        )
        
        return min(engagement, 1.0)


# Global instance
collaboration_service = HumanAICollaborationService()

