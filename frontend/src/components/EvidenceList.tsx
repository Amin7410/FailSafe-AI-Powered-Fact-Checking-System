import React, { useState } from 'react';
import './EvidenceList.css';

interface EvidenceItem {
  source: string;
  title?: string;
  snippet?: string;
  score?: number;
  provenance_timestamp?: string;
}

interface EvidenceListProps {
  evidence: EvidenceItem[];
  className?: string;
}

const EvidenceList: React.FC<EvidenceListProps> = ({ evidence, className = '' }) => {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#27ae60'; // Green
    if (score >= 0.6) return '#f39c12'; // Orange
    return '#e74c3c'; // Red
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  };

  if (!evidence || evidence.length === 0) {
    return (
      <div className={`evidence-list empty ${className}`}>
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <div className="empty-title">No Evidence Found</div>
          <div className="empty-description">
            Unable to find supporting evidence for this claim
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`evidence-list ${className}`}>
      <div className="evidence-header">
        <h3 className="evidence-title">
          📚 Evidence Sources ({evidence.length})
        </h3>
        <div className="evidence-summary">
          {evidence.length > 0 && (
            <span className="evidence-count">
              {evidence.length} source{evidence.length !== 1 ? 's' : ''} found
            </span>
          )}
        </div>
      </div>

      <div className="evidence-items">
        {evidence.map((item, index) => {
          const isExpanded = expandedItems.has(index);
          const score = item.score || 0;
          const scoreColor = getScoreColor(score);
          const scoreLabel = getScoreLabel(score);

          return (
            <div key={index} className="evidence-item">
              <div 
                className="evidence-item-header"
                onClick={() => toggleExpanded(index)}
              >
                <div className="evidence-source">
                  <div className="source-url">
                    {item.source}
                  </div>
                  {item.title && (
                    <div className="source-title">
                      {item.title}
                    </div>
                  )}
                </div>
                
                <div className="evidence-meta">
                  {item.score !== undefined && (
                    <div 
                      className="evidence-score"
                      style={{ color: scoreColor }}
                    >
                      <span className="score-label">{scoreLabel}</span>
                      <span className="score-value">
                        {Math.round(score * 100)}%
                      </span>
                    </div>
                  )}
                  
                  <div className="expand-icon">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="evidence-item-content">
                  {item.snippet && (
                    <div className="evidence-snippet">
                      <div className="snippet-label">Excerpt:</div>
                      <div className="snippet-text">
                        "{item.snippet}"
                      </div>
                    </div>
                  )}
                  
                  {item.provenance_timestamp && (
                    <div className="evidence-timestamp">
                      <span className="timestamp-label">Retrieved:</span>
                      <span className="timestamp-value">
                        {new Date(item.provenance_timestamp).toLocaleString()}
                      </span>
                    </div>
                  )}
                  
                  <div className="evidence-actions">
                    <a 
                      href={item.source} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="view-source-btn"
                    >
                      View Source
                    </a>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EvidenceList;
