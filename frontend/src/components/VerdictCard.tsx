import React from 'react';
import './VerdictCard.css';

interface VerdictCardProps {
  verdict: 'true' | 'false' | 'mixed' | 'unverifiable';
  confidence: number;
  className?: string;
}

const VerdictCard: React.FC<VerdictCardProps> = ({ verdict, confidence, className = '' }) => {
  const getVerdictConfig = () => {
    switch (verdict) {
      case 'true':
        return {
          label: 'TRUE',
          icon: '✅',
          color: '#27ae60',
          bgColor: '#d5f4e6',
          description: 'This claim is verified as true'
        };
      case 'false':
        return {
          label: 'FALSE',
          icon: '❌',
          color: '#e74c3c',
          bgColor: '#fadbd8',
          description: 'This claim is verified as false'
        };
      case 'mixed':
        return {
          label: 'MIXED',
          icon: '⚠️',
          color: '#f39c12',
          bgColor: '#fef9e7',
          description: 'This claim has mixed evidence'
        };
      case 'unverifiable':
        return {
          label: 'UNVERIFIABLE',
          icon: '❓',
          color: '#95a5a6',
          bgColor: '#f8f9fa',
          description: 'Insufficient evidence to verify'
        };
      default:
        return {
          label: 'UNKNOWN',
          icon: '❓',
          color: '#95a5a6',
          bgColor: '#f8f9fa',
          description: 'Unable to determine verdict'
        };
    }
  };

  const config = getVerdictConfig();
  const confidencePercentage = Math.round(confidence * 100);

  return (
    <div className={`verdict-card ${className}`} style={{ backgroundColor: config.bgColor }}>
      <div className="verdict-header">
        <span className="verdict-icon">{config.icon}</span>
        <span 
          className="verdict-label" 
          style={{ color: config.color }}
        >
          {config.label}
        </span>
      </div>
      
      <div className="verdict-description">
        {config.description}
      </div>
      
      <div className="confidence-section">
        <div className="confidence-label">Confidence Level</div>
        <div className="confidence-bar">
          <div 
            className="confidence-fill"
            style={{ 
              width: `${confidencePercentage}%`,
              backgroundColor: config.color
            }}
          />
        </div>
        <div className="confidence-percentage">
          {confidencePercentage}%
        </div>
      </div>
      
      <div className="verdict-footer">
        <span className="verdict-timestamp">
          Verified at {new Date().toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default VerdictCard;
