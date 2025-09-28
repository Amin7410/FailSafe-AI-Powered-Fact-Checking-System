// FailSafe Extension Options Script

class FailSafeOptions {
    constructor() {
        this.defaultSettings = {
            apiUrl: 'http://localhost:8000',
            autoHighlight: true,
            showConfidence: true,
            enableNotifications: true,
            anonymizeData: false,
            storeHistory: true
        };
        
        this.init();
    }

    async init() {
        await this.loadSettings();
        this.setupEventListeners();
        this.updateUI();
    }

    async loadSettings() {
        const settings = await chrome.storage.sync.get(this.defaultSettings);
        this.settings = settings;
    }

    async saveSettings() {
        const settings = {
            apiUrl: document.getElementById('apiUrl').value,
            autoHighlight: document.getElementById('autoHighlight').checked,
            showConfidence: document.getElementById('showConfidence').checked,
            enableNotifications: document.getElementById('enableNotifications').checked,
            anonymizeData: document.getElementById('anonymizeData').checked,
            storeHistory: document.getElementById('storeHistory').checked
        };

        await chrome.storage.sync.set(settings);
        this.settings = settings;
    }

    setupEventListeners() {
        // Save settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
            this.showStatus('Settings saved successfully!', 'success');
        });

        // Reset settings
        document.getElementById('resetSettings').addEventListener('click', () => {
            this.resetSettings();
        });

        // Test connection
        document.getElementById('testConnection').addEventListener('click', () => {
            this.testConnection();
        });

        // Clear history
        document.getElementById('clearHistory').addEventListener('click', () => {
            this.clearHistory();
        });

        // Export data
        document.getElementById('exportData').addEventListener('click', () => {
            this.exportData();
        });

        // Footer links
        document.getElementById('openWebApp').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: this.settings.apiUrl });
        });

        document.getElementById('openHelp').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: `${this.settings.apiUrl}/docs` });
        });
    }

    updateUI() {
        document.getElementById('apiUrl').value = this.settings.apiUrl;
        document.getElementById('autoHighlight').checked = this.settings.autoHighlight;
        document.getElementById('showConfidence').checked = this.settings.showConfidence;
        document.getElementById('enableNotifications').checked = this.settings.enableNotifications;
        document.getElementById('anonymizeData').checked = this.settings.anonymizeData;
        document.getElementById('storeHistory').checked = this.settings.storeHistory;
    }

    async testConnection() {
        const apiUrl = document.getElementById('apiUrl').value;
        const statusDiv = document.getElementById('connectionStatus');
        
        statusDiv.style.display = 'block';
        statusDiv.className = 'status info';
        statusDiv.textContent = 'Testing connection...';

        try {
            const response = await fetch(`${apiUrl}/api/v1/health`, {
                method: 'GET',
                timeout: 5000
            });

            if (response.ok) {
                statusDiv.className = 'status success';
                statusDiv.textContent = 'Connection successful!';
            } else {
                statusDiv.className = 'status error';
                statusDiv.textContent = `Connection failed: ${response.status} ${response.statusText}`;
            }
        } catch (error) {
            statusDiv.className = 'status error';
            statusDiv.textContent = `Connection failed: ${error.message}`;
        }
    }

    async resetSettings() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            await chrome.storage.sync.clear();
            await this.loadSettings();
            this.updateUI();
            this.showStatus('Settings reset to defaults', 'success');
        }
    }

    async clearHistory() {
        if (confirm('Are you sure you want to clear all analysis history? This cannot be undone.')) {
            await chrome.storage.local.remove('analyses');
            this.showStatus('Analysis history cleared', 'success');
        }
    }

    async exportData() {
        try {
            const { analyses = [] } = await chrome.storage.local.get('analyses');
            
            if (analyses.length === 0) {
                this.showStatus('No analysis data to export', 'info');
                return;
            }

            const data = {
                exportDate: new Date().toISOString(),
                version: '1.0.0',
                analyses: analyses
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `failsafe-analysis-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showStatus('Data exported successfully', 'success');
        } catch (error) {
            this.showStatus(`Export failed: ${error.message}`, 'error');
        }
    }

    showStatus(message, type) {
        const statusDiv = document.getElementById('saveStatus');
        statusDiv.style.display = 'block';
        statusDiv.className = `status ${type}`;
        statusDiv.textContent = message;

        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize options page
document.addEventListener('DOMContentLoaded', () => {
    new FailSafeOptions();
});

