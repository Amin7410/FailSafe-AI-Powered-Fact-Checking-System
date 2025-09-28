// FailSafe Browser Extension Content Script

class FailSafeContentScript {
    constructor() {
        this.isInitialized = false;
        this.highlightedElements = [];
        this.analysisResults = null;
        
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.setupMessageListener();
        this.setupKeyboardShortcuts();
        this.injectStyles();
        this.isInitialized = true;
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.action) {
                case 'highlightClaims':
                    this.highlightClaims();
                    sendResponse({ success: true });
                    break;
                case 'clearHighlights':
                    this.clearHighlights();
                    sendResponse({ success: true });
                    break;
                case 'analyzeSelection':
                    this.analyzeSelection();
                    sendResponse({ success: true });
                    break;
                case 'getPageText':
                    sendResponse({ text: this.getPageText() });
                    break;
                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+F for fact check
            if (e.ctrlKey && e.shiftKey && e.key === 'F') {
                e.preventDefault();
                this.analyzeSelection();
            }
            
            // Ctrl+Shift+H for highlight
            if (e.ctrlKey && e.shiftKey && e.key === 'H') {
                e.preventDefault();
                this.highlightClaims();
            }
        });
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .failsafe-highlight {
                background-color: #fff3cd !important;
                border: 2px solid #ffc107 !important;
                border-radius: 4px !important;
                padding: 2px 4px !important;
                position: relative !important;
                cursor: pointer !important;
            }
            
            .failsafe-highlight:hover {
                background-color: #ffeaa7 !important;
            }
            
            .failsafe-tooltip {
                position: absolute !important;
                background: #333 !important;
                color: white !important;
                padding: 8px 12px !important;
                border-radius: 4px !important;
                font-size: 12px !important;
                z-index: 10000 !important;
                max-width: 300px !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
                pointer-events: none !important;
            }
            
            .failsafe-tooltip::after {
                content: '' !important;
                position: absolute !important;
                top: 100% !important;
                left: 50% !important;
                margin-left: -5px !important;
                border-width: 5px !important;
                border-style: solid !important;
                border-color: #333 transparent transparent transparent !important;
            }
            
            .failsafe-claim {
                background-color: #d1ecf1 !important;
                border-left: 4px solid #17a2b8 !important;
                padding: 8px 12px !important;
                margin: 4px 0 !important;
                border-radius: 0 4px 4px 0 !important;
            }
            
            .failsafe-fallacy {
                background-color: #f8d7da !important;
                border-left: 4px solid #dc3545 !important;
                padding: 8px 12px !important;
                margin: 4px 0 !important;
                border-radius: 0 4px 4px 0 !important;
            }
            
            .failsafe-evidence {
                background-color: #d4edda !important;
                border-left: 4px solid #28a745 !important;
                padding: 8px 12px !important;
                margin: 4px 0 !important;
                border-radius: 0 4px 4px 0 !important;
            }
        `;
        document.head.appendChild(style);
    }

    getPageText() {
        // Remove script and style elements
        const scripts = document.querySelectorAll('script, style, nav, header, footer, aside');
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = document.body.innerHTML;
        
        scripts.forEach(el => {
            const elements = tempDiv.querySelectorAll(el.tagName);
            elements.forEach(e => e.remove());
        });

        // Get text content
        const text = tempDiv.innerText || tempDiv.textContent || '';
        
        // Clean up text
        return text
            .replace(/\s+/g, ' ')
            .trim()
            .substring(0, 5000); // Limit to 5000 characters
    }

    analyzeSelection() {
        const selection = window.getSelection();
        if (selection.toString().trim()) {
            const text = selection.toString().trim();
            this.performAnalysis(text);
        } else {
            this.showNotification('Please select text to analyze', 'warning');
        }
    }

    async performAnalysis(text) {
        try {
            // Show loading indicator
            this.showNotification('Analyzing selected text...', 'info');
            
            // Send to background script for analysis
            const response = await chrome.runtime.sendMessage({
                action: 'analyzeText',
                text: text,
                url: window.location.href
            });

            if (response.success) {
                this.analysisResults = response.result;
                this.displayResults(response.result);
            } else {
                this.showNotification('Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showNotification('Analysis failed', 'error');
        }
    }

    displayResults(result) {
        // Create results overlay
        const overlay = document.createElement('div');
        overlay.id = 'failsafe-results-overlay';
        overlay.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: rgba(0, 0, 0, 0.5) !important;
            z-index: 10000 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        `;

        const modal = document.createElement('div');
        modal.style.cssText = `
            background: white !important;
            border-radius: 8px !important;
            padding: 20px !important;
            max-width: 600px !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        `;

        modal.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #333;">Fact Check Results</h3>
                <button id="failsafe-close" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
            </div>
            <div id="failsafe-results-content">
                ${this.formatResults(result)}
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Close button
        document.getElementById('failsafe-close').addEventListener('click', () => {
            overlay.remove();
        });

        // Click outside to close
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    formatResults(result) {
        const verdictClass = result.verdict.toLowerCase();
        const confidence = Math.round(result.confidence * 100);
        
        let html = `
            <div class="failsafe-claim">
                <strong>Verdict:</strong> <span style="color: ${verdictClass === 'true' ? 'green' : verdictClass === 'false' ? 'red' : 'orange'}">${result.verdict.toUpperCase()}</span>
                <br>
                <strong>Confidence:</strong> ${confidence}%
            </div>
        `;

        if (result.evidence && result.evidence.length > 0) {
            html += `
                <div class="failsafe-evidence">
                    <strong>Evidence (${result.evidence.length} sources):</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        ${result.evidence.map(ev => `
                            <li>
                                <strong>${ev.title || 'Untitled'}</strong>
                                ${ev.score ? ` (${Math.round(ev.score * 100)}%)` : ''}
                                <br>
                                <small>${ev.snippet}</small>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        if (result.fallacies && result.fallacies.length > 0) {
            html += `
                <div class="failsafe-fallacy">
                    <strong>Logical Fallacies Detected (${result.fallacies.length}):</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        ${result.fallacies.map(f => `
                            <li>
                                <strong>${f.type.replace(/_/g, ' ')}</strong>
                                ${f.explanation ? `<br><small>${f.explanation}</small>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        if (result.ai_detection) {
            const aiClass = result.ai_detection.is_ai_generated ? 'failsafe-fallacy' : 'failsafe-evidence';
            html += `
                <div class="${aiClass}">
                    <strong>AI Detection:</strong> ${result.ai_detection.is_ai_generated ? 'Likely AI Generated' : 'Likely Human Written'}
                    (${Math.round(result.ai_detection.confidence * 100)}% confidence)
                </div>
            `;
        }

        return html;
    }

    highlightClaims() {
        this.clearHighlights();
        
        // Simple heuristic to find potential claims
        const textNodes = this.getTextNodes();
        const claims = this.extractClaims(textNodes);
        
        claims.forEach(claim => {
            this.highlightElement(claim.element, claim.text, claim.type);
        });

        this.showNotification(`Highlighted ${claims.length} potential claims`, 'success');
    }

    getTextNodes() {
        const textNodes = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    // Skip script and style elements
                    const parent = node.parentElement;
                    if (parent && (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim().length > 20) {
                textNodes.push(node);
            }
        }

        return textNodes;
    }

    extractClaims(textNodes) {
        const claims = [];
        const claimPatterns = [
            /(?:is|are|was|were|will be|should be|must be|can be)\s+[^.!?]*[.!?]/gi,
            /(?:always|never|all|every|none|no one|everyone)\s+[^.!?]*[.!?]/gi,
            /(?:studies show|research proves|experts say|scientists agree)\s+[^.!?]*[.!?]/gi,
            /(?:according to|based on|evidence suggests)\s+[^.!?]*[.!?]/gi
        ];

        textNodes.forEach(node => {
            const text = node.textContent;
            claimPatterns.forEach(pattern => {
                const matches = text.match(pattern);
                if (matches) {
                    matches.forEach(match => {
                        if (match.length > 20 && match.length < 200) {
                            claims.push({
                                element: node.parentElement,
                                text: match.trim(),
                                type: 'claim'
                            });
                        }
                    });
                }
            });
        });

        return claims;
    }

    highlightElement(element, text, type) {
        if (!element || element.classList.contains('failsafe-highlight')) return;

        element.classList.add('failsafe-highlight');
        element.setAttribute('data-failsafe-text', text);
        element.setAttribute('data-failsafe-type', type);

        // Add click handler for tooltip
        element.addEventListener('click', (e) => {
            e.preventDefault();
            this.showTooltip(e.target, text, type);
        });

        this.highlightedElements.push(element);
    }

    showTooltip(element, text, type) {
        // Remove existing tooltip
        const existingTooltip = document.querySelector('.failsafe-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }

        const tooltip = document.createElement('div');
        tooltip.className = 'failsafe-tooltip';
        tooltip.textContent = `Potential ${type}: ${text.substring(0, 100)}${text.length > 100 ? '...' : ''}`;

        document.body.appendChild(tooltip);

        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - 10}px`;

        // Remove tooltip after 3 seconds
        setTimeout(() => {
            tooltip.remove();
        }, 3000);
    }

    clearHighlights() {
        this.highlightedElements.forEach(element => {
            element.classList.remove('failsafe-highlight');
            element.removeAttribute('data-failsafe-text');
            element.removeAttribute('data-failsafe-type');
        });
        this.highlightedElements = [];

        // Remove tooltips
        const tooltips = document.querySelectorAll('.failsafe-tooltip');
        tooltips.forEach(tooltip => tooltip.remove());
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#4caf50'} !important;
            color: white !important;
            padding: 12px 16px !important;
            border-radius: 4px !important;
            font-size: 14px !important;
            z-index: 10001 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize content script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new FailSafeContentScript();
    });
} else {
    new FailSafeContentScript();
}

