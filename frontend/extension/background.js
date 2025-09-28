// FailSafe Browser Extension Background Script

class FailSafeBackground {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupInstallListener();
        this.loadSettings();
    }

    async loadSettings() {
        const settings = await chrome.storage.sync.get({
            apiUrl: 'http://localhost:8000'
        });
        this.apiUrl = settings.apiUrl;
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.action) {
                case 'analyzeText':
                    this.analyzeText(request.text, request.url)
                        .then(result => sendResponse({ success: true, result }))
                        .catch(error => sendResponse({ success: false, error: error.message }));
                    return true; // Keep message channel open for async response
                
                case 'checkApiHealth':
                    this.checkApiHealth()
                        .then(healthy => sendResponse({ healthy }))
                        .catch(() => sendResponse({ healthy: false }));
                    return true;
                
                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        });
    }

    setupInstallListener() {
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.showWelcomeNotification();
            }
        });
    }

    async analyzeText(text, url) {
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
                        source: 'browser_extension',
                        url: url,
                        timestamp: new Date().toISOString()
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Save analysis to storage
            await this.saveAnalysis(result, url);
            
            return result;
        } catch (error) {
            console.error('Analysis failed:', error);
            throw error;
        }
    }

    async checkApiHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/health`, {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    async saveAnalysis(result, url) {
        const analysis = {
            id: result.claim_id || Date.now().toString(),
            result: result,
            url: url,
            timestamp: new Date().toISOString()
        };

        const { analyses = [] } = await chrome.storage.local.get('analyses');
        analyses.unshift(analysis);
        
        // Keep only last 100 analyses
        if (analyses.length > 100) {
            analyses.splice(100);
        }

        await chrome.storage.local.set({ analyses });
    }

    showWelcomeNotification() {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'FailSafe Extension Installed',
            message: 'Click the FailSafe icon to start fact-checking web content!'
        });
    }
}

// Initialize background script
new FailSafeBackground();

