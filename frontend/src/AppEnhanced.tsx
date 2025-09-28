import React, { useState } from 'react';
import axios from 'axios';
import VerdictCard from './components/VerdictCard';
import EvidenceList from './components/EvidenceList';
import FallacyAlert from './components/FallacyAlert';
import './AppEnhanced.css';

interface EvidenceItem {
  source: string;
  title?: string;
  snippet?: string;
  score?: number;
  provenance_timestamp?: string;
  source_type?: string;
}

interface Verification {
  confidence: number;
  method: string;
  notes?: string;
}

interface AIDetection {
  is_ai_generated: boolean;
  confidence: number;
  method: string;
  scores: Record<string, number>;
  details: Record<string, any>;
}

interface FallacyItem {
  type: string;
  span?: string;
  explanation?: string;
}

interface MultilingualData {
  detected_language: string;
  processing_language: string;
  translation_info?: {
    translated_text: string;
    source_language: string;
    target_language: string;
    confidence: number;
    method: string;
  };
  cross_lingual_mappings: Array<{
    source_concept: string;
    target_concept: string;
    source_language: string;
    target_language: string;
    confidence: number;
    method: string;
  }>;
  supported_languages: string[];
}

interface ReportResponse {
  claim_id?: string;
  verdict: 'true' | 'false' | 'mixed' | 'unverifiable';
  confidence: number;
  evidence: EvidenceItem[];
  verification: Verification;
  fallacies: FallacyItem[];
  ai_detection?: AIDetection;
  multilingual?: MultilingualData;
  provenance: Record<string, any>;
}

const AppEnhanced: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [inputUrl, setInputUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisTime, setAnalysisTime] = useState<number | null>(null);

  const analyzeClaim = async () => {
    if (!inputText.trim() && !inputUrl.trim()) {
      setError('Please enter text or URL to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setReport(null);
    setAnalysisTime(null);

    const startTime = Date.now();

    try {
      const payload = {
        text: inputText.trim() || undefined,
        url: inputUrl.trim() || undefined,
        language,
        metadata: {
          source: 'web_interface',
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent
        }
      };

      const response = await axios.post<ReportResponse>(
        'http://localhost:8000/api/v1/analyze',
        payload,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 30000, // 30 seconds timeout
        }
      );

      const endTime = Date.now();
      setAnalysisTime(endTime - startTime);
      setReport(response.data);
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'An error occurred during analysis. Please try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const clearAnalysis = () => {
    setInputText('');
    setInputUrl('');
    setReport(null);
    setError(null);
    setAnalysisTime(null);
  };

  const getLanguageName = (code: string) => {
    const languages: Record<string, string> = {
      'en': 'English',
      'vi': 'Vietnamese',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German',
      'zh': 'Chinese',
      'ja': 'Japanese',
      'ko': 'Korean',
      'ar': 'Arabic',
      'hi': 'Hindi'
    };
    return languages[code] || code;
  };

  return (
    <div className="app-enhanced">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            🛡️ FailSafe
          </h1>
          <p className="app-subtitle">
            AI-Powered Fact-Checking & Misinformation Analysis
          </p>
        </div>
      </header>

      <main className="app-main">
        <div className="analysis-section">
          <div className="input-container">
            <div className="input-group">
              <label htmlFor="text-input" className="input-label">
                📝 Text to Analyze
              </label>
              <textarea
                id="text-input"
                className="text-input"
                placeholder="Enter the claim or statement you want to fact-check..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                rows={4}
                disabled={isAnalyzing}
              />
            </div>

            <div className="input-divider">
              <span>OR</span>
            </div>

            <div className="input-group">
              <label htmlFor="url-input" className="input-label">
                🔗 URL to Analyze
              </label>
              <input
                id="url-input"
                type="url"
                className="url-input"
                placeholder="https://example.com/article"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                disabled={isAnalyzing}
              />
            </div>

            <div className="input-group">
              <label htmlFor="language-select" className="input-label">
                🌐 Language
              </label>
              <select
                id="language-select"
                className="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="en">English</option>
                <option value="vi">Vietnamese</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="zh">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="ar">Arabic</option>
                <option value="hi">Hindi</option>
              </select>
            </div>

            <div className="action-buttons">
              <button
                className="analyze-btn"
                onClick={analyzeClaim}
                disabled={isAnalyzing || (!inputText.trim() && !inputUrl.trim())}
              >
                {isAnalyzing ? (
                  <>
                    <span className="spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  <>
                    🔍 Analyze Claim
                  </>
                )}
              </button>

              <button
                className="clear-btn"
                onClick={clearAnalysis}
                disabled={isAnalyzing}
              >
                🗑️ Clear
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <div className="error-icon">❌</div>
            <div className="error-content">
              <div className="error-title">Analysis Failed</div>
              <div className="error-text">{error}</div>
            </div>
          </div>
        )}

        {report && (
          <div className="results-section">
            <div className="results-header">
              <h2 className="results-title">📊 Analysis Results</h2>
              {analysisTime && (
                <div className="analysis-time">
                  Analyzed in {analysisTime}ms
                </div>
              )}
            </div>

            <div className="results-content">
              <VerdictCard
                verdict={report.verdict}
                confidence={report.confidence}
                className="main-verdict"
              />

              {report.ai_detection && (
                <div className="ai-detection-section">
                  <h3 className="section-title">🤖 AI Detection</h3>
                  <div className={`ai-detection-card ${report.ai_detection.is_ai_generated ? 'ai-generated' : 'human-written'}`}>
                    <div className="ai-detection-header">
                      <span className="ai-detection-icon">
                        {report.ai_detection.is_ai_generated ? '🤖' : '👤'}
                      </span>
                      <span className="ai-detection-label">
                        {report.ai_detection.is_ai_generated ? 'AI Generated' : 'Human Written'}
                      </span>
                    </div>
                    <div className="ai-detection-confidence">
                      Confidence: {Math.round(report.ai_detection.confidence * 100)}%
                    </div>
                    <div className="ai-detection-method">
                      Method: {report.ai_detection.method}
                    </div>
                  </div>
                </div>
              )}

              {report.multilingual && (
                <div className="multilingual-section">
                  <h3 className="section-title">🌐 Language Analysis</h3>
                  <div className="multilingual-card">
                    <div className="language-info">
                      <div className="language-item">
                        <span className="language-label">Detected:</span>
                        <span className="language-value">
                          {getLanguageName(report.multilingual.detected_language)}
                        </span>
                      </div>
                      <div className="language-item">
                        <span className="language-label">Processed:</span>
                        <span className="language-value">
                          {getLanguageName(report.multilingual.processing_language)}
                        </span>
                      </div>
                    </div>
                    {report.multilingual.translation_info && (
                      <div className="translation-info">
                        <div className="translation-label">Translation Applied</div>
                        <div className="translation-details">
                          {report.multilingual.translation_info.source_language} → {report.multilingual.translation_info.target_language}
                          <span className="translation-confidence">
                            ({Math.round(report.multilingual.translation_info.confidence * 100)}% confidence)
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <EvidenceList
                evidence={report.evidence}
                className="main-evidence"
              />

              <FallacyAlert
                fallacies={report.fallacies}
                className="main-fallacies"
              />

              <div className="verification-section">
                <h3 className="section-title">🔍 Verification Details</h3>
                <div className="verification-card">
                  <div className="verification-method">
                    <span className="method-label">Method:</span>
                    <span className="method-value">{report.verification.method}</span>
                  </div>
                  {report.verification.notes && (
                    <div className="verification-notes">
                      <span className="notes-label">Notes:</span>
                      <span className="notes-value">{report.verification.notes}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>🛡️ FailSafe - Making the internet a more truthful place</p>
          <div className="footer-links">
            <a href="/api/v1/docs/" target="_blank" rel="noopener noreferrer">
              API Documentation
            </a>
            <a href="/api/v1/health" target="_blank" rel="noopener noreferrer">
              System Health
            </a>
            <a href="/api/v1/monitor/status" target="_blank" rel="noopener noreferrer">
              Performance
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AppEnhanced;
