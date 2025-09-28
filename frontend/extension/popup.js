// FailSafe Browser Extension Popup Script

class FailSafePopup {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.currentTab = null;
        this.isAnalyzing = false;
        
        this.init();
    }

    async init() {
        await this.loadSettings();
        await this.getCurrentTab();
        this.setupEventListeners();
        this.updatePageInfo();
        this.updateStatus();
    }

    async loadSettings() {
        const settings = await chrome.storage.sync.get({
            autoHighlight: true,
            showConfidence: true,
            enableNotifications: true,
            apiUrl: 'http://localhost:8000'
        });
        
        this.settings = settings;
        this.apiUrl = settings.apiUrl;
        
        // Update UI
        document.getElementById('autoHighlight').checked = settings.autoHighlight;
        document.getElementById('showConfidence').checked = settings.showConfidence;
        document.getElementById('enableNotifications').checked = settings.enableNotifications;
    }

    async saveSettings() {
        const settings = {
            autoHighlight: document.getElementById('autoHighlight').checked,
            showConfidence: document.getElementById('showConfidence').checked,
            enableNotifications: document.getElementById('enableNotifications').checked,
            apiUrl: this.apiUrl
        };
        
        await chrome.storage.sync.set(settings);
        this.settings = settings;
    }

    async getCurrentTab() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        this.currentTab = tab;
    }

    setupEventListeners() {
        // Quick analysis
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeText();
        });

        // Page analysis
        document.getElementById('analyzePageBtn').addEventListener('click', () => {
            this.analyzePage();
        });

        // Highlight claims
        document.getElementById('highlightBtn').addEventListener('click', () => {
            this.highlightClaims();
        });

        // Settings
        document.getElementById('openOptions').addEventListener('click', () => {
            chrome.runtime.openOptionsPage();
        });

        // Footer links
        document.getElementById('openWebApp').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: this.apiUrl });
        });

        document.getElementById('openHelp').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: `${this.apiUrl}/docs` });
        });

        // Settings change
        ['autoHighlight', 'showConfidence', 'enableNotifications'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.saveSettings();
            });
        });

        // Enter key for quick analysis
        document.getElementById('quickText').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.analyzeText();
            }
        });
    }

    updatePageInfo() {
        if (this.currentTab) {
            document.getElementById('pageUrl').textContent = this.currentTab.url;
            document.getElementById('pageTitle').textContent = this.currentTab.title || 'Untitled';
        }
    }

    updateStatus() {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        if (this.isAnalyzing) {
            statusDot.className = 'status-dot warning';
            statusText.textContent = 'Analyzing...';
        } else {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Ready';
        }
    }

    async analyzeText() {
        const text = document.getElementById('quickText').value.trim();
        if (!text) {
            this.showNotification('Please enter text to analyze', 'warning');
            return;
        }

        await this.performAnalysis(text, 'text');
    }

    async analyzePage() {
        if (!this.currentTab) {
            this.showNotification('Unable to access current page', 'error');
            return;
        }

        // Extract text from page
        const results = await chrome.scripting.executeScript({
            target: { tabId: this.currentTab.id },
            function: this.extractPageText
        });

        const text = results[0]?.result || '';
        if (!text.trim()) {
            this.showNotification('No text found on this page', 'warning');
            return;
        }

        await this.performAnalysis(text, 'page');
    }

    async performAnalysis(text, source) {
        if (this.isAnalyzing) return;

        this.isAnalyzing = true;
        this.updateStatus();
        this.showLoading(true);

        try {
            const response = await fetch(`${this.apiUrl}/api/v1/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    language: 'en',
                    metadata: {
                        source: source,
                        url: this.currentTab?.url,
                        timestamp: new Date().toISOString()
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.displayResults(result);

            // Save analysis to storage
            await this.saveAnalysis(result, source);

            if (this.settings.enableNotifications) {
                this.showNotification('Analysis completed!', 'success');
            }

        } catch (error) {
            console.error('Analysis failed:', error);
            this.showNotification('Analysis failed. Please try again.', 'error');
        } finally {
            this.isAnalyzing = false;
            this.updateStatus();
            this.showLoading(false);
        }
    }

    displayResults(result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');
        
        resultsSection.style.display = 'block';
        resultsContainer.innerHTML = '';

        // Main result
        const mainResult = this.createResultElement(result, true);
        resultsContainer.appendChild(mainResult);

        // Evidence
        if (result.evidence && result.evidence.length > 0) {
            const evidenceSection = document.createElement('div');
            evidenceSection.className = 'result-item';
            evidenceSection.innerHTML = `
                <div class="result-header">
                    <span class="result-verdict">Evidence (${result.evidence.length})</span>
                </div>
                <div class="result-evidence">
                    ${result.evidence.map(ev => `
                        <div style="margin-bottom: 8px;">
                            <strong>${ev.title || 'Untitled'}</strong>
                            ${this.settings.showConfidence ? `<span class="result-confidence">(${Math.round(ev.score * 100)}%)</span>` : ''}
                            <br>
                            <small>${ev.snippet}</small>
                        </div>
                    `).join('')}
                </div>
            `;
            resultsContainer.appendChild(evidenceSection);
        }

        // Fallacies
        if (result.fallacies && result.fallacies.length > 0) {
            const fallaciesSection = document.createElement('div');
            fallaciesSection.className = 'result-item';
            fallaciesSection.innerHTML = `
                <div class="result-header">
                    <span class="result-verdict">Logical Fallacies (${result.fallacies.length})</span>
                </div>
                <div class="result-fallacies">
                    ${result.fallacies.map(f => `
                        <span class="fallacy-item">${f.type.replace(/_/g, ' ')}</span>
                    `).join('')}
                </div>
            `;
            resultsContainer.appendChild(fallaciesSection);
        }

        // AI Detection
        if (result.ai_detection) {
            const aiSection = document.createElement('div');
            aiSection.className = 'result-item';
            aiSection.innerHTML = `
                <div class="result-header">
                    <span class="result-verdict ${result.ai_detection.is_ai_generated ? 'false' : 'true'}">
                        ${result.ai_detection.is_ai_generated ? 'AI Generated' : 'Human Written'}
                    </span>
                    ${this.settings.showConfidence ? `<span class="result-confidence">${Math.round(result.ai_detection.confidence * 100)}%</span>` : ''}
                </div>
            `;
            resultsContainer.appendChild(aiSection);
        }
    }

    createResultElement(result, isMain = false) {
        const element = document.createElement('div');
        element.className = 'result-item';
        
        const verdictClass = result.verdict.toLowerCase();
        const confidence = this.settings.showConfidence ? 
            `<span class="result-confidence">${Math.round(result.confidence * 100)}%</span>` : '';

        element.innerHTML = `
            <div class="result-header">
                <span class="result-verdict ${verdictClass}">${result.verdict.toUpperCase()}</span>
                ${confidence}
            </div>
            <div class="result-text">${result.verdict}</div>
        `;

        return element;
    }

    async highlightClaims() {
        if (!this.currentTab) {
            this.showNotification('Unable to access current page', 'error');
            return;
        }

        try {
            await chrome.scripting.executeScript({
                target: { tabId: this.currentTab.id },
                function: this.highlightClaimsOnPage
            });

            this.showNotification('Claims highlighted on page', 'success');
        } catch (error) {
            console.error('Highlighting failed:', error);
            this.showNotification('Failed to highlight claims', 'error');
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#4caf50'};
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async saveAnalysis(result, source) {
        const analysis = {
            id: result.claim_id || Date.now().toString(),
            result: result,
            source: source,
            timestamp: new Date().toISOString(),
            url: this.currentTab?.url
        };

        const { analyses = [] } = await chrome.storage.local.get('analyses');
        analyses.unshift(analysis);
        
        // Keep only last 50 analyses
        if (analyses.length > 50) {
            analyses.splice(50);
        }

        await chrome.storage.local.set({ analyses });
    }

    // Functions to be injected into page
    extractPageText() {
        // Remove script and style elements
        const scripts = document.querySelectorAll('script, style, nav, header, footer, aside');
        scripts.forEach(el => el.remove());

        // Get text content
        const text = document.body.innerText || document.body.textContent || '';
        
        // Clean up text
        return text
            .replace(/\s+/g, ' ')
            .trim()
            .substring(0, 5000); // Limit to 5000 characters
    }

    highlightClaimsOnPage() {
        // This would be implemented to highlight claims on the page
        // For now, just show a simple highlight
        const text = document.body.innerText;
        const sentences = text.split(/[.!?]+/);
        
        sentences.forEach(sentence => {
            if (sentence.length > 20 && sentence.length < 200) {
                // Simple heuristic: highlight sentences that might be claims
                if (sentence.includes('is') || sentence.includes('are') || 
                    sentence.includes('will') || sentence.includes('should')) {
                    // This is a simplified version - in reality, you'd want more sophisticated highlighting
                    console.log('Potential claim:', sentence.trim());
                }
            }
        });
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FailSafePopup();
});






