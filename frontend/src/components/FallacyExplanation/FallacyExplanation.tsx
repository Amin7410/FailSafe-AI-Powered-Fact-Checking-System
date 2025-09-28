import React, { useState } from 'react';
import './FallacyExplanation.css';

interface FallacyExplanationProps {
  fallacy: {
    type: string;
    explanation?: string;
    span?: string;
    confidence?: number;
    severity?: 'low' | 'medium' | 'high';
  };
  onClose?: () => void;
  onFeedback?: (feedback: any) => void;
}

export const FallacyExplanation: React.FC<FallacyExplanationProps> = ({
  fallacy,
  onClose,
  onFeedback
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [userComment, setUserComment] = useState('');

  const getFallacyInfo = (type: string) => {
    const fallacies: Record<string, {
      name: string;
      description: string;
      examples: string[];
      howToAvoid: string[];
      severity: 'low' | 'medium' | 'high';
      category: string;
    }> = {
      'ad_hominem': {
        name: 'Ad Hominem',
        description: 'Attacking the person making the argument rather than addressing the argument itself.',
        examples: [
          'You can\'t trust his opinion on climate change because he\'s not a scientist.',
          'She\'s just saying that because she\'s a liberal.',
          'Don\'t listen to him, he\'s just trying to sell you something.'
        ],
        howToAvoid: [
          'Focus on the argument, not the person',
          'Address the evidence and reasoning',
          'Ask for specific examples or data'
        ],
        severity: 'high',
        category: 'Personal Attack'
      },
      'straw_man': {
        name: 'Straw Man',
        description: 'Misrepresenting someone\'s argument to make it easier to attack.',
        examples: [
          'So you\'re saying we should just let criminals run free?',
          'You want to destroy the economy with these regulations.',
          'They\'re basically saying we should abandon all our values.'
        ],
        howToAvoid: [
          'Accurately represent the other person\'s position',
          'Ask for clarification if unsure',
          'Address the strongest version of their argument'
        ],
        severity: 'high',
        category: 'Misrepresentation'
      },
      'cherry_picking': {
        name: 'Cherry Picking',
        description: 'Selectively choosing data or evidence that supports your position while ignoring contradictory evidence.',
        examples: [
          'This study shows the treatment works (ignoring 10 other studies that show it doesn\'t)',
          'Look at these statistics from 2019 (ignoring more recent data)',
          'Here\'s one expert who agrees with me (ignoring the consensus)'
        ],
        howToAvoid: [
          'Present all relevant evidence',
          'Acknowledge contradictory data',
          'Explain why certain evidence is more reliable'
        ],
        severity: 'high',
        category: 'Selective Evidence'
      },
      'hasty_generalization': {
        name: 'Hasty Generalization',
        description: 'Drawing a broad conclusion from insufficient evidence.',
        examples: [
          'All politicians are corrupt (based on one scandal)',
          'This diet works for everyone (based on one success story)',
          'The whole system is broken (based on one bad experience)'
        ],
        howToAvoid: [
          'Gather more evidence before generalizing',
          'Consider sample size and representativeness',
          'Use qualifiers like "some" or "many" instead of "all"'
        ],
        severity: 'medium',
        category: 'Insufficient Evidence'
      },
      'false_dilemma': {
        name: 'False Dilemma',
        description: 'Presenting only two options when more exist, forcing a false choice.',
        examples: [
          'You\'re either with us or against us',
          'Either we cut taxes or the economy will collapse',
          'It\'s either freedom or security, you can\'t have both'
        ],
        howToAvoid: [
          'Look for additional options or alternatives',
          'Question whether the choices are mutually exclusive',
          'Consider compromise or middle-ground solutions'
        ],
        severity: 'medium',
        category: 'False Choice'
      },
      'slippery_slope': {
        name: 'Slippery Slope',
        description: 'Arguing that a small step will inevitably lead to a chain of events ending in a significant effect.',
        examples: [
          'If we allow same-sex marriage, next people will want to marry animals',
          'If we ban this book, soon all books will be banned',
          'If we raise the minimum wage, businesses will all close down'
        ],
        howToAvoid: [
          'Provide evidence for each step in the chain',
          'Show that the final outcome is likely, not just possible',
          'Consider whether the slope is actually slippery'
        ],
        severity: 'medium',
        category: 'Causal Chain'
      },
      'appeal_to_authority': {
        name: 'Appeal to Authority',
        description: 'Using an authority figure\'s opinion as evidence when they\'re not an expert in the relevant field.',
        examples: [
          'Einstein believed in God, so God must exist',
          'My doctor says this political policy is wrong',
          'A famous actor endorses this medical treatment'
        ],
        howToAvoid: [
          'Check if the authority is relevant to the topic',
          'Look for consensus among experts in the field',
          'Consider the authority\'s potential biases'
        ],
        severity: 'low',
        category: 'Authority'
      },
      'appeal_to_emotion': {
        name: 'Appeal to Emotion',
        description: 'Using emotional language or stories to persuade rather than logical reasoning.',
        examples: [
          'Think of the children! We must pass this law',
          'This policy is heartless and cruel',
          'How can you sleep at night supporting this?'
        ],
        howToAvoid: [
          'Focus on facts and evidence',
          'Use emotional appeals to support, not replace, logic',
          'Acknowledge emotions while maintaining objectivity'
        ],
        severity: 'low',
        category: 'Emotional Manipulation'
      }
    };

    return fallacies[type] || {
      name: type.replace(/_/g, ' ').toUpperCase(),
      description: 'A logical fallacy that weakens the argument.',
      examples: [],
      howToAvoid: [],
      severity: 'medium',
      category: 'Unknown'
    };
  };

  const fallacyInfo = getFallacyInfo(fallback.type);
  const severity = fallacy.severity || fallacyInfo.severity;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return '#dc3545';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (userRating && onFeedback) {
      onFeedback({
        type: 'fallacy_detection',
        rating: userRating,
        comment: userComment.trim() || undefined,
        specific_element: fallacy.type
      });
      setUserRating(null);
      setUserComment('');
    }
  };

  return (
    <div className="fallacy-explanation">
      <div className="fallacy-header">
        <div className="fallacy-title">
          <span className="fallacy-icon">
            {getSeverityIcon(severity)}
          </span>
          <h3>{fallacyInfo.name}</h3>
          <span 
            className="severity-badge"
            style={{ backgroundColor: getSeverityColor(severity) }}
          >
            {severity.toUpperCase()}
          </span>
        </div>
        
        <div className="fallacy-actions">
          <button 
            className="btn btn-outline btn-sm"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
          {onClose && (
            <button 
              className="btn btn-close btn-sm"
              onClick={onClose}
            >
              ×
            </button>
          )}
        </div>
      </div>

      <div className="fallacy-content">
        <div className="fallacy-description">
          <p>{fallacyInfo.description}</p>
        </div>

        {fallacy.span && (
          <div className="fallacy-detected-text">
            <h4>Detected Text:</h4>
            <blockquote>"{fallacy.span}"</blockquote>
          </div>
        )}

        {fallacy.confidence && (
          <div className="fallacy-confidence">
            <h4>Detection Confidence:</h4>
            <div className="confidence-bar">
              <div 
                className="confidence-fill"
                style={{ 
                  width: `${fallacy.confidence * 100}%`,
                  backgroundColor: getSeverityColor(severity)
                }}
              />
              <span className="confidence-text">
                {Math.round(fallback.confidence * 100)}%
              </span>
            </div>
          </div>
        )}

        {showDetails && (
          <div className="fallacy-details">
            <div className="detail-section">
              <h4>Examples</h4>
              <ul className="examples-list">
                {fallacyInfo.examples.map((example, index) => (
                  <li key={index} className="example-item">
                    {example}
                  </li>
                ))}
              </ul>
            </div>

            <div className="detail-section">
              <h4>How to Avoid</h4>
              <ul className="avoid-list">
                {fallacyInfo.howToAvoid.map((tip, index) => (
                  <li key={index} className="avoid-item">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>

            <div className="detail-section">
              <h4>Category</h4>
              <span className="category-badge">
                {fallacyInfo.category}
              </span>
            </div>
          </div>
        )}

        {onFeedback && (
          <div className="fallacy-feedback">
            <h4>Rate This Detection</h4>
            <form onSubmit={handleFeedbackSubmit} className="feedback-form">
              <div className="rating-section">
                <label>How accurate is this detection?</label>
                <div className="rating-buttons">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      className={`rating-btn ${userRating === rating ? 'selected' : ''}`}
                      onClick={() => setUserRating(rating)}
                    >
                      {rating}
                    </button>
                  ))}
                </div>
                <div className="rating-labels">
                  <span>Very Poor</span>
                  <span>Excellent</span>
                </div>
              </div>

              <div className="comment-section">
                <label htmlFor="comment">Additional Comments (optional)</label>
                <textarea
                  id="comment"
                  value={userComment}
                  onChange={(e) => setUserComment(e.target.value)}
                  placeholder="Share your thoughts about this fallacy detection..."
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={!userRating}
                >
                  Submit Feedback
                </button>
                <button 
                  type="button" 
                  className="btn btn-outline"
                  onClick={() => {
                    setUserRating(null);
                    setUserComment('');
                  }}
                >
                  Clear
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};






