"""
Provenance Tracking API Endpoints

Provides access to provenance data for transparency and auditability.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.provenance_service import provenance_tracker, ProvenanceType, SourceType
from app.models.report import ReportResponse

router = APIRouter(prefix="/provenance")


@router.get("/entries")
def get_provenance_entries(
    type: Optional[ProvenanceType] = Query(None, description="Filter by provenance type"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip")
) -> Dict[str, Any]:
    """Get provenance entries with optional filtering"""
    try:
        entries = provenance_tracker.entries
        
        # Apply filters
        if type:
            entries = [e for e in entries if e.type == type]
        if session_id:
            entries = [e for e in entries if e.session_id == session_id]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        
        # Apply pagination
        total = len(entries)
        entries = entries[offset:offset + limit]
        
        return {
            "entries": [entry.to_dict() for entry in entries],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{entry_id}")
def get_provenance_entry(entry_id: str = Path(..., description="Provenance entry ID")) -> Dict[str, Any]:
    """Get a specific provenance entry by ID"""
    try:
        entry = provenance_tracker.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return entry.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{entry_id}/chain")
def get_provenance_chain(entry_id: str = Path(..., description="Provenance entry ID")) -> Dict[str, Any]:
    """Get the complete provenance chain for an entry"""
    try:
        entry = provenance_tracker.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        chain = provenance_tracker.get_chain(entry_id)
        
        return {
            "entry_id": entry_id,
            "chain": [entry.to_dict() for entry in chain],
            "chain_length": len(chain)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{entry_id}/evidence")
def get_evidence_chain(entry_id: str = Path(..., description="Provenance entry ID")) -> Dict[str, Any]:
    """Get the evidence chain for an output entry"""
    try:
        entry = provenance_tracker.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        evidence_chain = provenance_tracker.get_evidence_chain(entry_id)
        
        return {
            "entry_id": entry_id,
            "evidence_chain": [entry.to_dict() for entry in evidence_chain],
            "evidence_count": len(evidence_chain)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
def get_session_provenance(session_id: str = Path(..., description="Session ID")) -> Dict[str, Any]:
    """Get all provenance entries for a session"""
    try:
        return provenance_tracker.export_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
def get_user_provenance(user_id: str = Path(..., description="User ID")) -> Dict[str, Any]:
    """Get all provenance entries for a user (GDPR compliance)"""
    try:
        return provenance_tracker.export_user_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/anonymize")
def anonymize_user_data(user_id: str = Path(..., description="User ID")) -> Dict[str, str]:
    """Anonymize user data (GDPR compliance)"""
    try:
        success = provenance_tracker.anonymize_user_data(user_id)
        if success:
            return {"message": f"User data anonymized successfully for user {user_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to anonymize user data")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
def get_provenance_statistics() -> Dict[str, Any]:
    """Get provenance statistics"""
    try:
        return provenance_tracker.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
def get_provenance_types() -> Dict[str, List[str]]:
    """Get available provenance types and source types"""
    return {
        "provenance_types": [t.value for t in ProvenanceType],
        "source_types": [t.value for t in SourceType]
    }


@router.get("/health")
def provenance_health_check() -> Dict[str, Any]:
    """Health check for provenance tracking system"""
    try:
        stats = provenance_tracker.get_statistics()
        return {
            "status": "healthy",
            "total_entries": stats["total_entries"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

