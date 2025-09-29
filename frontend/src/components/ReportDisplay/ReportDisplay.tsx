import React, { useState } from 'react';
import { ReportResponse } from '../../types/Report';
import './ReportDisplay.css';

interface ReportDisplayProps {
  report: ReportResponse;
  onFeedback?: (feedback: any) => void;
  onOverride?: (override: any) => void;
  showDetails?: boolean;
}

export const ReportDisplay: React.FC<ReportDisplayProps> = ({
  report,
  onFeedback,
  onOverride,
  showDetails = true
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'evidence' | 'fallacies' | 'sag' | 'provenance'>('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict.toLowerCase()) {
      case 'true': return '#28a745';
      case 'false': return '#dc3545';
      case 'mixed': return '#ffc107';
      case 'unverifiable': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.8) return { level: 'High', color: '#28a745' };
    if (confidence >= 0.6) return { level: 'Medium', color: '#ffc107' };
    return { level: 'Low', color: '#dc3545' };
  };

  const confidenceInfo = getConfidenceLevel(report.confidence);

  return (
    <div className="report-display">
      {/* Header */}
      <div className="report-header">
        <div className="verdict-section">
          <div 
            className="verdict-badge"
            style={{ backgroundColor: getVerdictColor(report.verdict) }}
          >
            {report.verdict.toUpperCase()}
          </div>
          <div className="confidence-section">
            <span className="confidence-label">Confidence:</span>
            <span 
              className="confidence-value"
              style={{ color: confidenceInfo.color }}
            >
              {Math.round(report.confidence * 100)}% ({confidenceInfo.level})
            </span>
          </div>
          <div className="indicator-badges">
            {/* Bias indicator (placeholder) */}
            <span className="badge bias" title="Potential source bias indicator">BIAS</span>
            {/* Hallucination indicator derived from verification notes (placeholder parse) */}
            {report.verification.notes && report.verification.notes.includes('hallucination_risk=high') ? (
              <span className="badge hallucination" title="High hallucination risk">HALLUCINATION</span>
            ) : null}
          </div>
        </div>
        
        {onFeedback && (
          <div className="action-buttons">
            <button 
              className="btn btn-outline"
              onClick={() => onFeedback({ type: 'accuracy', rating: 0 })}
            >
              Rate Accuracy
            </button>
            <button 
              className="btn btn-outline"
              onClick={() => onOverride({ type: 'verdict', original: report.verdict })}
            >
              Override
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="report-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          Evidence ({report.evidence.length})
        </button>
        <button 
          className={`tab ${activeTab === 'fallacies' ? 'active' : ''}`}
          onClick={() => setActiveTab('fallacies')}
        >
          Fallacies ({report.fallacies.length})
        </button>
        {report.sag && (
          <button 
            className={`tab ${activeTab === 'sag' ? 'active' : ''}`}
            onClick={() => setActiveTab('sag')}
          >
            SAG
          </button>
        )}
        <button 
          className={`tab ${activeTab === 'provenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('provenance')}
        >
          Provenance
        </button>
      </div>

      {/* Content */}
      <div className="report-content">
        {activeTab === 'overview' && (
          <OverviewTab 
            report={report}
            expandedSections={expandedSections}
            onToggleSection={toggleSection}
            onFeedback={onFeedback}
            onOverride={onOverride}
          />
        )}
        
        {activeTab === 'evidence' && (
          <EvidenceTab 
            evidence={report.evidence}
            onFeedback={onFeedback}
          />
        )}
        
        {activeTab === 'fallacies' && (
          <FallaciesTab 
            fallacies={report.fallacies}
            onFeedback={onFeedback}
          />
        )}
        
        {activeTab === 'sag' && report.sag && (
          <SAGTab 
            sag={report.sag}
            expandedSections={expandedSections}
            onToggleSection={toggleSection}
          />
        )}
        
        {activeTab === 'provenance' && (
          <ProvenanceTab 
            provenance={report.provenance}
            reportId={report.claim_id}
          />
        )}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<{
  report: ReportResponse;
  expandedSections: Set<string>;
  onToggleSection: (id: string) => void;
  onFeedback?: (feedback: any) => void;
  onOverride?: (override: any) => void;
}> = ({ report, expandedSections, onToggleSection, onFeedback, onOverride }) => {
  return (
    <div className="overview-tab">
      {/* Verification Details */}
      <CollapsibleSection
        id="verification"
        title="Verification Details"
        expanded={expandedSections.has('verification')}
        onToggle={() => onToggleSection('verification')}
      >
        <div className="verification-details">
          <div className="verification-method">
            <strong>Method:</strong> {report.verification.method}
          </div>
          <div className="verification-confidence">
            <strong>Confidence:</strong> {Math.round(report.verification.confidence * 100)}%
          </div>
          {report.verification.notes && (
            <div className="verification-notes">
              <strong>Notes:</strong> {report.verification.notes}
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* AI Detection */}
      {report.ai_detection && (
        <CollapsibleSection
          id="ai-detection"
          title="AI Detection"
          expanded={expandedSections.has('ai-detection')}
          onToggle={() => onToggleSection('ai-detection')}
        >
          <div className="ai-detection-details">
            <div className={`ai-result ${report.ai_detection.is_ai_generated ? 'ai-generated' : 'human-written'}`}>
              {report.ai_detection.is_ai_generated ? '🤖 AI Generated' : '👤 Human Written'}
              <span className="confidence">
                ({Math.round(report.ai_detection.confidence * 100)}%)
              </span>
            </div>
            <div className="ai-method">
              <strong>Method:</strong> {report.ai_detection.method}
            </div>
            {Object.keys(report.ai_detection.scores).length > 0 && (
              <div className="ai-scores">
                <strong>Detection Scores:</strong>
                <ul>
                  {Object.entries(report.ai_detection.scores).map(([key, score]) => (
                    <li key={key}>
                      {key}: {score.toFixed(3)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* Multilingual Support */}
      {report.multilingual && (
        <CollapsibleSection
          id="multilingual"
          title="Multilingual Analysis"
          expanded={expandedSections.has('multilingual')}
          onToggle={() => onToggleSection('multilingual')}
        >
          <div className="multilingual-details">
            <div className="language-info">
              <strong>Detected:</strong> {report.multilingual.detected_language}
              <br />
              <strong>Processing:</strong> {report.multilingual.processing_language}
            </div>
            {report.multilingual.translation_info && (
              <div className="translation-info">
                <strong>Translation:</strong> {report.multilingual.translation_info.source_language} → {report.multilingual.translation_info.target_language}
                <br />
                <strong>Confidence:</strong> {Math.round(report.multilingual.translation_info.confidence * 100)}%
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* Human Feedback Section */}
      {onFeedback && (
        <CollapsibleSection
          id="feedback"
          title="Provide Feedback"
          expanded={expandedSections.has('feedback')}
          onToggle={() => onToggleSection('feedback')}
        >
          <FeedbackForm onFeedback={onFeedback} />
        </CollapsibleSection>
      )}
    </div>
  );
};

// Evidence Tab Component
const EvidenceTab: React.FC<{
  evidence: any[];
  onFeedback?: (feedback: any) => void;
}> = ({ evidence, onFeedback }) => {
  return (
    <div className="evidence-tab">
      {evidence.length === 0 ? (
        <div className="no-evidence">
          <p>No evidence found for this claim.</p>
        </div>
      ) : (
        <div className="evidence-list">
          {evidence.map((item, index) => (
            <div key={index} className="evidence-item">
              <div className="evidence-header">
                <h4>
                  <a href={item.source} target="_blank" rel="noopener noreferrer">
                    {item.title || 'Untitled Source'}
                  </a>
                </h4>
                <div className="evidence-score">
                  Score: {item.score ? Math.round(item.score * 100) : 'N/A'}%
                </div>
              </div>
              <div className="evidence-snippet">
                {item.snippet}
              </div>
              <div className="evidence-meta">
                <span className="source-type">{item.source_type || 'Unknown'}</span>
                {item.provenance_timestamp && (
                  <span className="timestamp">
                    {new Date(item.provenance_timestamp).toLocaleString()}
                  </span>
                )}
              </div>
              {onFeedback && (
                <div className="evidence-actions">
                  <button 
                    className="btn btn-sm btn-outline"
                    onClick={() => onFeedback({ 
                      type: 'source_quality', 
                      rating: 0, 
                      specific_element: item.source 
                    })}
                  >
                    Rate Source
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Fallacies Tab Component
const FallaciesTab: React.FC<{
  fallacies: any[];
  onFeedback?: (feedback: any) => void;
}> = ({ fallacies, onFeedback }) => {
  const getSeverityColor = (type: string) => {
    if (type.includes('ad_hominem') || type.includes('straw_man') || type.includes('cherry_picking')) {
      return '#dc3545'; // High severity
    }
    if (type.includes('hasty_generalization') || type.includes('false_dilemma') || type.includes('slippery_slope')) {
      return '#ffc107'; // Medium severity
    }
    return '#28a745'; // Low severity
  };

  const getSeverityIcon = (type: string) => {
    if (type.includes('ad_hominem') || type.includes('straw_man') || type.includes('cherry_picking')) {
      return '🔴';
    }
    if (type.includes('hasty_generalization') || type.includes('false_dilemma') || type.includes('slippery_slope')) {
      return '🟡';
    }
    return '🟢';
  };

  return (
    <div className="fallacies-tab">
      {fallacies.length === 0 ? (
        <div className="no-fallacies">
          <p>No logical fallacies detected.</p>
        </div>
      ) : (
        <div className="fallacies-list">
          {fallacies.map((fallacy, index) => (
            <div key={index} className="fallacy-item">
              <div className="fallacy-header">
                <span className="fallacy-icon">
                  {getSeverityIcon(fallacy.type)}
                </span>
                <h4 className="fallacy-type">
                  {fallacy.type.replace(/_/g, ' ').toUpperCase()}
                </h4>
                <span 
                  className="fallacy-severity"
                  style={{ color: getSeverityColor(fallacy.type) }}
                >
                  {fallacy.type.includes('ad_hominem') || fallacy.type.includes('straw_man') || fallacy.type.includes('cherry_picking') ? 'HIGH' : 
                   fallacy.type.includes('hasty_generalization') || fallacy.type.includes('false_dilemma') || fallacy.type.includes('slippery_slope') ? 'MEDIUM' : 'LOW'}
                </span>
              </div>
              {fallacy.explanation && (
                <div className="fallacy-explanation">
                  {fallacy.explanation}
                </div>
              )}
              {fallacy.span && (
                <div className="fallacy-span">
                  <strong>Detected text:</strong> "{fallacy.span}"
                </div>
              )}
              {onFeedback && (
                <div className="fallacy-actions">
                  <button 
                    className="btn btn-sm btn-outline"
                    onClick={() => onFeedback({ 
                      type: 'logical_flow', 
                      rating: 0, 
                      specific_element: fallacy.type 
                    })}
                  >
                    Rate Detection
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// SAG Tab Component
const SAGTab: React.FC<{
  sag: any;
  expandedSections: Set<string>;
  onToggleSection: (id: string) => void;
}> = ({ sag, expandedSections, onToggleSection }) => {
  return (
    <div className="sag-tab">
      <CollapsibleSection
        id="sag-overview"
        title="SAG Overview"
        expanded={expandedSections.has('sag-overview')}
        onToggle={() => onToggleSection('sag-overview')}
      >
        <div className="sag-overview">
          <div className="sag-info">
            <div><strong>Analysis ID:</strong> {sag.analysis_id}</div>
            <div><strong>Language:</strong> {sag.language}</div>
            <div><strong>Nodes:</strong> {sag.nodes.length}</div>
            <div><strong>Edges:</strong> {sag.edges.length}</div>
            <div><strong>Format:</strong> {sag.metadata?.format || 'rdf_owl_subset'}</div>
          </div>
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        id="sag-nodes"
        title="Nodes"
        expanded={expandedSections.has('sag-nodes')}
        onToggle={() => onToggleSection('sag-nodes')}
      >
        <div className="sag-nodes">
          {sag.nodes.slice(0, 10).map((node: any, index: number) => (
            <div key={index} className="sag-node">
              <div className="node-id">{node.id}</div>
              <div className="node-type">{node.type}</div>
              <div className="node-label">{node.label}</div>
            </div>
          ))}
          {sag.nodes.length > 10 && (
            <div className="more-nodes">
              ... and {sag.nodes.length - 10} more nodes
            </div>
          )}
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        id="sag-edges"
        title="Edges"
        expanded={expandedSections.has('sag-edges')}
        onToggle={() => onToggleSection('sag-edges')}
      >
        <div className="sag-edges">
          {sag.edges.slice(0, 10).map((edge: any, index: number) => (
            <div key={index} className="sag-edge">
              <div className="edge-relation">
                {edge.source} → {edge.target}
              </div>
              <div className="edge-type">{edge.relation}</div>
            </div>
          ))}
          {sag.edges.length > 10 && (
            <div className="more-edges">
              ... and {sag.edges.length - 10} more edges
            </div>
          )}
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        id="sag-rdf"
        title="RDF Data"
        expanded={expandedSections.has('sag-rdf')}
        onToggle={() => onToggleSection('sag-rdf')}
      >
        <div className="sag-rdf">
          {Object.entries(sag.rdf_graph).map(([format, content]) => (
            <div key={format} className="rdf-format">
              <strong>{format}:</strong> {content ? `${content.length} characters` : 'Empty'}
            </div>
          ))}
        </div>
      </CollapsibleSection>
    </div>
  );
};

// Provenance Tab Component
const ProvenanceTab: React.FC<{
  provenance: any;
  reportId?: string | null;
}> = ({ provenance, reportId }) => {
  return (
    <div className="provenance-tab">
      <div className="provenance-info">
        <h4>Analysis Provenance</h4>
        <div className="provenance-details">
          <div><strong>Report ID:</strong> {reportId || 'Unknown'}</div>
          <div><strong>Generated:</strong> {new Date().toLocaleString()}</div>
          <div><strong>Source:</strong> FailSafe Analysis Engine</div>
        </div>
      </div>
      
      <div className="provenance-actions">
        <button className="btn btn-outline">
          View Full Provenance Chain
        </button>
        <button className="btn btn-outline">
          Export Provenance Data
        </button>
      </div>
    </div>
  );
};

// Collapsible Section Component
const CollapsibleSection: React.FC<{
  id: string;
  title: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}> = ({ id, title, expanded, onToggle, children }) => {
  return (
    <div className="collapsible-section">
      <button 
        className="section-header"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <span className="section-title">{title}</span>
        <span className="section-toggle">
          {expanded ? '▼' : '▶'}
        </span>
      </button>
      {expanded && (
        <div className="section-content">
          {children}
        </div>
      )}
    </div>
  );
};

// Feedback Form Component
const FeedbackForm: React.FC<{
  onFeedback: (feedback: any) => void;
}> = ({ onFeedback }) => {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFeedback({
      type: 'accuracy',
      rating,
      comment: comment.trim() || undefined
    });
    setRating(0);
    setComment('');
  };

  return (
    <form className="feedback-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Rate this analysis (1-5):</label>
        <div className="rating-input">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              className={`rating-btn ${rating >= value ? 'active' : ''}`}
              onClick={() => setRating(value)}
            >
              {value}
            </button>
          ))}
        </div>
      </div>
      <div className="form-group">
        <label>Comments (optional):</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share your thoughts about this analysis..."
          rows={3}
        />
      </div>
      <button type="submit" className="btn btn-primary">
        Submit Feedback
      </button>
    </form>
  );
};

