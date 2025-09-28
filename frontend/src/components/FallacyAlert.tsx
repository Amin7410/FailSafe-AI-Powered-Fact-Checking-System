import React, { useState } from 'react';
import './FallacyAlert.css';

interface FallacyItem {
  type: string;
  span?: string;
  explanation?: string;
}

interface FallacyAlertProps {
  fallacies: FallacyItem[];
  className?: string;
}

const FallacyAlert: React.FC<FallacyAlertProps> = ({ fallacies, className = '' }) => {
  const [expandedFallacies, setExpandedFallacies] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedFallacies);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedFallacies(newExpanded);
  };

  const getFallacyConfig = (type: string) => {
    const configs: Record<string, any> = {
      'hasty_generalization': {
        icon: '🚀',
        label: 'Hasty Generalization',
        color: '#e74c3c',
        bgColor: '#fadbd8',
        description: 'Making broad conclusions from limited evidence'
      },
      'ad_hominem': {
        icon: '👤',
        label: 'Ad Hominem',
        color: '#e67e22',
        bgColor: '#fdeaa7',
        description: 'Attacking the person instead of the argument'
      },
      'straw_man': {
        icon: '🌾',
        label: 'Straw Man',
        color: '#f39c12',
        bgColor: '#fef9e7',
        description: 'Misrepresenting someone\'s argument to make it easier to attack'
      },
      'false_dilemma': {
        icon: '⚖️',
        label: 'False Dilemma',
        color: '#9b59b6',
        bgColor: '#f4ecf7',
        description: 'Presenting only two options when more exist'
      },
      'slippery_slope': {
        icon: '⛷️',
        label: 'Slippery Slope',
        color: '#1abc9c',
        bgColor: '#d5f4e6',
        description: 'Assuming one event will lead to a chain of events'
      },
      'appeal_to_authority': {
        icon: '👨‍🎓',
        label: 'Appeal to Authority',
        color: '#3498db',
        bgColor: '#d6eaf8',
        description: 'Using authority as evidence without proper context'
      },
      'cherry_picking': {
        icon: '🍒',
        label: 'Cherry Picking',
        color: '#e91e63',
        bgColor: '#fce4ec',
        description: 'Selectively choosing evidence that supports your position'
      },
      'correlation_causation': {
        icon: '🔗',
        label: 'Correlation vs Causation',
        color: '#ff9800',
        bgColor: '#fff3e0',
        description: 'Confusing correlation with causation'
      },
      'appeal_to_emotion': {
        icon: '💝',
        label: 'Appeal to Emotion',
        color: '#f44336',
        bgColor: '#ffebee',
        description: 'Using emotional manipulation instead of logical reasoning'
      },
      'red_herring': {
        icon: '🐟',
        label: 'Red Herring',
        color: '#607d8b',
        bgColor: '#eceff1',
        description: 'Introducing irrelevant information to distract from the main issue'
      }
    };

    return configs[type] || {
      icon: '⚠️',
      label: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      color: '#95a5a6',
      bgColor: '#f8f9fa',
      description: 'Logical fallacy detected'
    };
  };

  if (!fallacies || fallacies.length === 0) {
    return (
      <div className={`fallacy-alert no-fallacies ${className}`}>
        <div className="no-fallacies-content">
          <div className="no-fallacies-icon">✅</div>
          <div className="no-fallacies-title">No Logical Fallacies Detected</div>
          <div className="no-fallacies-description">
            The analysis found no logical fallacies in this claim
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`fallacy-alert ${className}`}>
      <div className="fallacy-header">
        <h3 className="fallacy-title">
          ⚠️ Logical Fallacies Detected ({fallacies.length})
        </h3>
        <div className="fallacy-summary">
          {fallacies.length} logical error{fallacies.length !== 1 ? 's' : ''} found
        </div>
      </div>

      <div className="fallacy-items">
        {fallacies.map((fallacy, index) => {
          const config = getFallacyConfig(fallacy.type);
          const isExpanded = expandedFallacies.has(index);

          return (
            <div 
              key={index} 
              className="fallacy-item"
              style={{ borderLeftColor: config.color }}
            >
              <div 
                className="fallacy-item-header"
                onClick={() => toggleExpanded(index)}
              >
                <div className="fallacy-info">
                  <div className="fallacy-icon">{config.icon}</div>
                  <div className="fallacy-details">
                    <div className="fallacy-label" style={{ color: config.color }}>
                      {config.label}
                    </div>
                    {fallacy.span && (
                      <div className="fallacy-span">
                        "{fallacy.span}"
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="fallacy-actions">
                  <div className="expand-icon">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="fallacy-item-content">
                  <div className="fallacy-description">
                    <div className="description-label">What is this fallacy?</div>
                    <div className="description-text">
                      {config.description}
                    </div>
                  </div>
                  
                  {fallacy.explanation && (
                    <div className="fallacy-explanation">
                      <div className="explanation-label">Analysis:</div>
                      <div className="explanation-text">
                        {fallacy.explanation}
                      </div>
                    </div>
                  )}
                  
                  <div className="fallacy-tips">
                    <div className="tips-label">💡 How to avoid this:</div>
                    <div className="tips-text">
                      {getFallacyTips(fallacy.type)}
                    </div>
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

const getFallacyTips = (type: string): string => {
  const tips: Record<string, string> = {
    'hasty_generalization': 'Look for sufficient evidence before making broad claims. Consider exceptions and counterexamples.',
    'ad_hominem': 'Focus on the argument itself, not the person making it. Address the content, not the character.',
    'straw_man': 'Represent arguments accurately and fairly. Address the strongest version of the opposing view.',
    'false_dilemma': 'Consider multiple options and alternatives. Look for middle ground or third options.',
    'slippery_slope': 'Examine each step in the chain. Consider if the progression is inevitable or likely.',
    'appeal_to_authority': 'Verify the authority\'s expertise in the relevant field. Check if they have a conflict of interest.',
    'cherry_picking': 'Present all relevant evidence, not just what supports your position. Acknowledge counterevidence.',
    'correlation_causation': 'Look for alternative explanations. Consider if there might be a third factor causing both.',
    'appeal_to_emotion': 'Use facts and logic to support your argument. Emotions can supplement but not replace reasoning.',
    'red_herring': 'Stay focused on the main issue. Address the original point rather than introducing tangents.'
  };

  return tips[type] || 'Consider the logical structure of your argument and ensure your reasoning is sound.';
};

export default FallacyAlert;
