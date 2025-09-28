"""
Provenance Tracking Service

Tracks the origin, processing history, and verification chain of all data
and analysis results to ensure transparency and auditability.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.config import get_settings


class ProvenanceType(Enum):
    """Types of provenance entries"""
    INPUT = "input"
    PROCESSING = "processing"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    ANALYSIS = "analysis"
    OUTPUT = "output"
    USER_FEEDBACK = "user_feedback"
    ERROR = "error"


class SourceType(Enum):
    """Types of data sources"""
    URL = "url"
    TEXT = "text"
    FILE = "file"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    USER_INPUT = "user_input"
    AI_MODEL = "ai_model"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class ProvenanceEntry:
    """Single provenance entry"""
    id: str
    timestamp: datetime
    type: ProvenanceType
    source_type: SourceType
    source_id: str
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    operation: str = ""
    parameters: Optional[Dict[str, Any]] = None
    input_data_hash: Optional[str] = None
    output_data_hash: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    parent_ids: List[str] = None
    child_ids: List[str] = None
    tags: List[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []
        if self.child_ids is None:
            self.child_ids = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['type'] = self.type.value
        data['source_type'] = self.source_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceEntry':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['type'] = ProvenanceType(data['type'])
        data['source_type'] = SourceType(data['source_type'])
        return cls(**data)


class ProvenanceTracker:
    """Main provenance tracking service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.entries: List[ProvenanceEntry] = []
        self.entry_map: Dict[str, ProvenanceEntry] = {}
        self.session_id = str(uuid.uuid4())
    
    def create_entry(
        self,
        type: ProvenanceType,
        source_type: SourceType,
        source_id: str,
        operation: str = "",
        source_url: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        input_data_hash: Optional[str] = None,
        output_data_hash: Optional[str] = None,
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        parent_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Create a new provenance entry"""
        
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        entry = ProvenanceEntry(
            id=entry_id,
            timestamp=timestamp,
            type=type,
            source_type=source_type,
            source_id=source_id,
            source_url=source_url,
            source_metadata=source_metadata or {},
            operation=operation,
            parameters=parameters or {},
            input_data_hash=input_data_hash,
            output_data_hash=output_data_hash,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            parent_ids=parent_ids or [],
            child_ids=[],
            tags=tags or [],
            user_id=user_id,
            session_id=self.session_id
        )
        
        # Add to tracking
        self.entries.append(entry)
        self.entry_map[entry_id] = entry
        
        # Update parent-child relationships
        if parent_ids:
            for parent_id in parent_ids:
                if parent_id in self.entry_map:
                    self.entry_map[parent_id].child_ids.append(entry_id)
        
        return entry
    
    def track_input(
        self,
        source_id: str,
        source_type: SourceType,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track input data"""
        return self.create_entry(
            type=ProvenanceType.INPUT,
            source_type=source_type,
            source_id=source_id,
            operation="input_received",
            source_url=source_url,
            source_metadata=metadata,
            user_id=user_id
        )
    
    def track_processing(
        self,
        operation: str,
        source_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        input_data_hash: Optional[str] = None,  # <-- THÊM THAM SỐ NÀY
        output_data_hash: Optional[str] = None, # <-- THÊM THAM SỐ NÀY
        processing_time_ms: Optional[int] = None,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        source_type: SourceType = SourceType.AI_MODEL # <-- Thêm source_type mặc định
    ) -> ProvenanceEntry:
        """Track processing operation"""
        return self.create_entry(
            type=ProvenanceType.PROCESSING,
            source_type=source_type, # <-- Sử dụng source_type
            source_id=source_id,
            operation=operation,
            parameters=parameters,
            input_data_hash=input_data_hash,    # <-- Sử dụng tham số đã thêm
            output_data_hash=output_data_hash,  # <-- Sử dụng tham số đã thêm
            processing_time_ms=processing_time_ms,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_evidence(
        self,
        evidence_id: str,
        source_url: str,
        confidence_score: float,
        metadata: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track evidence retrieval"""
        return self.create_entry(
            type=ProvenanceType.EVIDENCE,
            source_type=SourceType.EXTERNAL_SERVICE,
            source_id=evidence_id,
            operation="evidence_retrieved",
            source_url=source_url,
            source_metadata=metadata,
            confidence_score=confidence_score,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_verification(
        self,
        verification_id: str,
        confidence_score: float,
        method: str,
        parameters: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track verification process"""
        return self.create_entry(
            type=ProvenanceType.VERIFICATION,
            source_type=SourceType.AI_MODEL,
            source_id=verification_id,
            operation=f"verification_{method}",
            parameters=parameters,
            confidence_score=confidence_score,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_analysis(
        self,
        analysis_id: str,
        operation: str,
        confidence_score: Optional[float] = None,
        parameters: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track analysis process"""
        return self.create_entry(
            type=ProvenanceType.ANALYSIS,
            source_type=SourceType.AI_MODEL,
            source_id=analysis_id,
            operation=operation,
            parameters=parameters,
            confidence_score=confidence_score,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_output(
        self,
        output_id: str,
        output_type: str,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track output generation"""
        return self.create_entry(
            type=ProvenanceType.OUTPUT,
            source_type=SourceType.AI_MODEL,
            source_id=output_id,
            operation=f"output_{output_type}",
            source_metadata=metadata,
            confidence_score=confidence_score,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_error(
        self,
        error_id: str,
        error_message: str,
        operation: str,
        parent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ProvenanceEntry:
        """Track error occurrence"""
        return self.create_entry(
            type=ProvenanceType.ERROR,
            source_type=SourceType.AI_MODEL,
            source_id=error_id,
            operation=operation,
            error_message=error_message,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def track_user_feedback(
        self,
        feedback_id: str,
        feedback_type: str,
        user_id: str,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProvenanceEntry:
        """Track user feedback"""
        return self.create_entry(
            type=ProvenanceType.USER_FEEDBACK,
            source_type=SourceType.USER_INPUT,
            source_id=feedback_id,
            operation=f"feedback_{feedback_type}",
            source_metadata=metadata,
            parent_ids=parent_ids,
            user_id=user_id
        )
    
    def get_entry(self, entry_id: str) -> Optional[ProvenanceEntry]:
        """Get specific entry by ID"""
        return self.entry_map.get(entry_id)
    
    def get_entries_by_type(self, type: ProvenanceType) -> List[ProvenanceEntry]:
        """Get all entries of specific type"""
        return [entry for entry in self.entries if entry.type == type]
    
    def get_entries_by_session(self, session_id: str) -> List[ProvenanceEntry]:
        """Get all entries for a session"""
        return [entry for entry in self.entries if entry.session_id == session_id]
    
    def get_entries_by_user(self, user_id: str) -> List[ProvenanceEntry]:
        """Get all entries for a user"""
        return [entry for entry in self.entries if entry.user_id == user_id]
    
    def get_chain(self, entry_id: str) -> List[ProvenanceEntry]:
        """Get the complete provenance chain for an entry"""
        chain = []
        visited = set()
        
        def build_chain(current_id: str):
            if current_id in visited or current_id not in self.entry_map:
                return
            
            visited.add(current_id)
            entry = self.entry_map[current_id]
            chain.append(entry)
            
            # Add parents
            for parent_id in entry.parent_ids:
                build_chain(parent_id)
        
        build_chain(entry_id)
        return sorted(chain, key=lambda x: x.timestamp)
    
    def get_evidence_chain(self, output_id: str) -> List[ProvenanceEntry]:
        """Get the evidence chain for an output"""
        evidence_entries = []
        visited = set()
        
        def find_evidence(current_id: str):
            if current_id in visited or current_id not in self.entry_map:
                return
            
            visited.add(current_id)
            entry = self.entry_map[current_id]
            
            if entry.type == ProvenanceType.EVIDENCE:
                evidence_entries.append(entry)
            
            # Check parents
            for parent_id in entry.parent_ids:
                find_evidence(parent_id)
        
        find_evidence(output_id)
        return sorted(evidence_entries, key=lambda x: x.timestamp)
    
    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export all entries for a session"""
        entries = self.get_entries_by_session(session_id)
        return {
            "session_id": session_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(entries),
            "entries": [entry.to_dict() for entry in entries]
        }
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all data for a user (GDPR compliance)"""
        entries = self.get_entries_by_user(user_id)
        return {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(entries),
            "entries": [entry.to_dict() for entry in entries]
        }
    
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data (GDPR compliance)"""
        entries = self.get_entries_by_user(user_id)
        for entry in entries:
            entry.user_id = None
            # Remove PII from metadata
            if entry.source_metadata:
                pii_fields = ['email', 'phone', 'name', 'address']
                for field in pii_fields:
                    entry.source_metadata.pop(field, None)
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get provenance statistics"""
        stats = {
            "total_entries": len(self.entries),
            "by_type": {},
            "by_source_type": {},
            "by_session": {},
            "error_rate": 0.0,
            "average_processing_time": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        total_processing_time = 0
        processing_count = 0
        error_count = 0
        
        for entry in self.entries:
            # Count by type
            type_name = entry.type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # Count by source type
            source_name = entry.source_type.value
            stats["by_source_type"][source_name] = stats["by_source_type"].get(source_name, 0) + 1
            
            # Count by session
            session = entry.session_id
            stats["by_session"][session] = stats["by_session"].get(session, 0) + 1
            
            # Error rate
            if entry.type == ProvenanceType.ERROR:
                error_count += 1
            
            # Processing time
            if entry.processing_time_ms:
                total_processing_time += entry.processing_time_ms
                processing_count += 1
            
            # Confidence distribution
            if entry.confidence_score:
                if entry.confidence_score >= 0.8:
                    stats["confidence_distribution"]["high"] += 1
                elif entry.confidence_score >= 0.6:
                    stats["confidence_distribution"]["medium"] += 1
                else:
                    stats["confidence_distribution"]["low"] += 1
        
        if len(self.entries) > 0:
            stats["error_rate"] = error_count / len(self.entries)
        
        if processing_count > 0:
            stats["average_processing_time"] = total_processing_time / processing_count
        
        return stats


# Global instance
provenance_tracker = ProvenanceTracker()

