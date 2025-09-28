"""
Database Models

SQLAlchemy models for the FailSafe database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Analysis(Base):
    """Analysis records"""
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    input_text = Column(Text, nullable=False)
    input_url = Column(String, nullable=True)
    language = Column(String, nullable=True)
    verdict = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    evidence_items = relationship("EvidenceItem", back_populates="analysis")
    fallacies = relationship("Fallacy", back_populates="analysis")
    feedback = relationship("Feedback", back_populates="analysis")
    overrides = relationship("Override", back_populates="analysis")


class EvidenceItem(Base):
    """Evidence items for analyses"""
    __tablename__ = "evidence_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    source = Column(String, nullable=False)
    title = Column(String, nullable=True)
    url = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=False)
    credibility_score = Column(Float, nullable=False)
    source_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="evidence_items")


class Fallacy(Base):
    """Detected fallacies"""
    __tablename__ = "fallacies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    location = Column(String, nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="fallacies")


class Feedback(Base):
    """User feedback"""
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    user_id = Column(String, nullable=True)
    feedback_type = Column(String, nullable=False)
    score = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="feedback")


class Override(Base):
    """User overrides"""
    __tablename__ = "overrides"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    user_id = Column(String, nullable=True)
    override_type = Column(String, nullable=False)
    original_value = Column(JSON, nullable=False)
    new_value = Column(JSON, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="overrides")


class ProvenanceEntry(Base):
    """Provenance tracking entries"""
    __tablename__ = "provenance_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)
    parent_ids = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    data_hash = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CollaborationSession(Base):
    """Collaboration sessions"""
    __tablename__ = "collaboration_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    analysis_id = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)


class SystemMetric(Base):
    """System metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_type = Column(String, nullable=False)
    component = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)


class Alert(Base):
    """System alerts"""
    __tablename__ = "alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    component = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True)
