"""
API Documentation Endpoints

Provides endpoints for:
1. API documentation
2. OpenAPI schema
3. API version info
4. Endpoint descriptions
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import json

router = APIRouter(prefix="/docs")


@router.get("/", response_class=HTMLResponse)
def get_api_docs():
    """Get API documentation HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FailSafe API Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
            .method { font-weight: bold; color: #007bff; }
            .path { font-family: monospace; background: #e9ecef; padding: 2px 5px; }
            .description { margin-top: 10px; }
            .example { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
            .status { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }
            .healthy { background: #d4edda; color: #155724; }
            .degraded { background: #fff3cd; color: #856404; }
            .unhealthy { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ FailSafe API Documentation</h1>
            <p>AI-powered fact-checking and misinformation analysis system</p>
        </div>
        
        <h2>📋 API Overview</h2>
        <p>FailSafe provides a comprehensive API for analyzing claims, detecting fallacies, and verifying information using advanced AI techniques.</p>
        
        <h2>🔗 Core Endpoints</h2>
        
        <div class="endpoint">
            <div class="method">POST</div>
            <div class="path">/api/v1/analyze</div>
            <div class="description">
                <strong>Analyze Claim</strong> - Main endpoint for fact-checking and analysis
                <br>Accepts text or URL input and returns comprehensive analysis including:
                <ul>
                    <li>Verification results with confidence scores</li>
                    <li>Evidence from reliable sources</li>
                    <li>Logical fallacy detection</li>
                    <li>AI-generated content detection</li>
                    <li>Multilingual support</li>
                </ul>
            </div>
            <div class="example">
                Request Body:
                {
                    "text": "Climate change is a hoax",
                    "language": "en",
                    "metadata": {"source": "social_media"}
                }
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/health</div>
            <div class="description">
                <strong>Health Check</strong> - System health and status information
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/monitor/status</div>
            <div class="description">
                <strong>System Status</strong> - Comprehensive system monitoring and performance metrics
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/monitor/performance</div>
            <div class="description">
                <strong>Performance Metrics</strong> - Detailed performance statistics and monitoring data
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/monitor/cache</div>
            <div class="description">
                <strong>Cache Statistics</strong> - Cache performance and hit/miss ratios
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/monitor/optimization</div>
            <div class="description">
                <strong>Optimization Suggestions</strong> - AI-powered performance optimization recommendations
            </div>
        </div>
        
        <h2>🔧 Development Endpoints</h2>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/feedback</div>
            <div class="description">
                <strong>Feedback Collection</strong> - User feedback and system improvement data
            </div>
        </div>
        
        <div class="endpoint">
            <div class="method">GET</div>
            <div class="path">/api/v1/pubmed</div>
            <div class="description">
                <strong>PubMed Integration</strong> - Scientific literature search and verification
            </div>
        </div>
        
        <h2>📊 Response Format</h2>
        <p>All analysis endpoints return structured JSON responses with the following format:</p>
        <div class="example">
            {
                "claim_id": "unique_identifier",
                "verdict": "true|false|mixed|unverifiable",
                "confidence": 0.85,
                "evidence": [...],
                "verification": {...},
                "fallacies": [...],
                "ai_detection": {...},
                "multilingual": {...},
                "provenance": {...}
            }
        </div>
        
        <h2>🌐 Multilingual Support</h2>
        <p>FailSafe supports multiple languages including English, Vietnamese, Spanish, French, German, Chinese, Japanese, Korean, Arabic, and Hindi.</p>
        
        <h2>⚡ Performance Features</h2>
        <ul>
            <li><strong>Caching:</strong> Intelligent caching system for improved response times</li>
            <li><strong>Monitoring:</strong> Real-time performance monitoring and health checks</li>
            <li><strong>Optimization:</strong> AI-powered optimization suggestions</li>
            <li><strong>Scalability:</strong> Designed for high-throughput production environments</li>
        </ul>
        
        <h2>🔒 Security & Ethics</h2>
        <ul>
            <li><strong>Rate Limiting:</strong> Configurable rate limits to prevent abuse</li>
            <li><strong>Privacy:</strong> GDPR-compliant data handling</li>
            <li><strong>Bias Detection:</strong> Built-in bias detection and mitigation</li>
            <li><strong>Transparency:</strong> Explainable AI with detailed reasoning</li>
        </ul>
        
        <h2>📚 Additional Resources</h2>
        <ul>
            <li><a href="/docs/openapi.json">OpenAPI Schema</a></li>
            <li><a href="/docs/redoc">ReDoc Documentation</a></li>
            <li><a href="/api/v1/health">Health Check</a></li>
            <li><a href="/api/v1/monitor/status">System Status</a></li>
        </ul>
        
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
            <h3>🚀 Getting Started</h3>
            <p>To start using the FailSafe API:</p>
            <ol>
                <li>Check system health: <code>GET /api/v1/health</code></li>
                <li>Analyze a claim: <code>POST /api/v1/analyze</code></li>
                <li>Monitor performance: <code>GET /api/v1/monitor/status</code></li>
            </ol>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/openapi.json")
def get_openapi_schema():
    """Get OpenAPI schema"""
    try:
        from fastapi.openapi.utils import get_openapi
        from app.main import app
        
        openapi_schema = get_openapi(
            title="FailSafe API",
            version="1.0.0",
            description="AI-powered fact-checking and misinformation analysis system",
            routes=app.routes,
        )
        
        return openapi_schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OpenAPI schema: {str(e)}")


@router.get("/version")
def get_api_version():
    """Get API version information"""
    return {
        "api_version": "1.0.0",
        "service_name": "FailSafe API",
        "description": "AI-powered fact-checking and misinformation analysis system",
        "features": [
            "Fact-checking and verification",
            "Logical fallacy detection",
            "AI-generated content detection",
            "Multilingual support",
            "Performance monitoring",
            "Caching system",
            "Real-time health checks"
        ],
        "supported_languages": [
            "en", "vi", "es", "fr", "de", "zh", "ja", "ko", "ar", "hi"
        ],
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "health": "/api/v1/health",
            "monitor": "/api/v1/monitor/*",
            "feedback": "/api/v1/feedback",
            "pubmed": "/api/v1/pubmed"
        }
    }


@router.get("/endpoints")
def get_endpoints_info():
    """Get detailed information about all endpoints"""
    return {
        "endpoints": [
            {
                "path": "/api/v1/analyze",
                "method": "POST",
                "description": "Main analysis endpoint for fact-checking",
                "parameters": {
                    "text": "string (optional) - Text content to analyze",
                    "url": "string (optional) - URL to fetch and analyze",
                    "language": "string (optional) - Language code (default: en)",
                    "metadata": "object (optional) - Additional metadata"
                },
                "response": "ReportResponse with analysis results"
            },
            {
                "path": "/api/v1/health",
                "method": "GET",
                "description": "System health check",
                "parameters": {},
                "response": "Health status information"
            },
            {
                "path": "/api/v1/monitor/status",
                "method": "GET",
                "description": "Comprehensive system status",
                "parameters": {},
                "response": "System status and performance metrics"
            },
            {
                "path": "/api/v1/monitor/performance",
                "method": "GET",
                "description": "Performance statistics",
                "parameters": {},
                "response": "Detailed performance metrics"
            },
            {
                "path": "/api/v1/monitor/cache",
                "method": "GET",
                "description": "Cache statistics",
                "parameters": {},
                "response": "Cache performance data"
            },
            {
                "path": "/api/v1/monitor/optimization",
                "method": "GET",
                "description": "Optimization suggestions",
                "parameters": {},
                "response": "AI-powered optimization recommendations"
            },
            {
                "path": "/api/v1/feedback",
                "method": "GET",
                "description": "Feedback collection",
                "parameters": {},
                "response": "User feedback data"
            },
            {
                "path": "/api/v1/pubmed",
                "method": "GET",
                "description": "PubMed integration",
                "parameters": {},
                "response": "Scientific literature data"
            }
        ]
    }
