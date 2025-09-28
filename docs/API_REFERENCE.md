# FailSafe API Reference

## Overview

The FailSafe API provides comprehensive fact-checking and misinformation analysis capabilities through a RESTful interface. This document describes all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication for development purposes. In production, API keys or OAuth2 tokens will be required.

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Burst**: 20 requests per 10 seconds
- **Headers**: Rate limit information is included in response headers

## Common Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "error": null
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and error details:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  }
}
```

## Endpoints

### Analysis

#### POST /analyze

Analyze a claim for fact-checking and misinformation detection.

**Request Body:**
```json
{
  "text": "The Earth is flat",
  "url": "https://example.com/article",
  "language": "en",
  "metadata": {
    "source": "user_input",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "claim_id": "uuid",
    "verdict": "false",
    "confidence": 0.95,
    "evidence": [
      {
        "source": "https://nasa.gov/earth",
        "title": "Earth is Round",
        "snippet": "Scientific evidence shows...",
        "score": 0.92,
        "source_type": "academic"
      }
    ],
    "verification": {
      "method": "scientific_consensus",
      "confidence": 0.95,
      "notes": "Overwhelming scientific evidence"
    },
    "fallacies": [
      {
        "type": "false_dilemma",
        "explanation": "Presents only two options",
        "confidence": 0.88
      }
    ],
    "ai_detection": {
      "is_ai_generated": false,
      "confidence": 0.15,
      "method": "ensemble_detection"
    },
    "multilingual": {
      "detected_language": "en",
      "processing_language": "en"
    },
    "sag": {
      "analysis_id": "uuid",
      "language": "en",
      "nodes": [...],
      "edges": [...],
      "rdf_graph": {...}
    },
    "provenance": {
      "analysis_id": "uuid",
      "timestamp": "2024-01-01T00:00:00Z",
      "source": "FailSafe Analysis Engine",
      "chain": [...]
    },
    "processing_time_ms": 1250
  }
}
```

### Provenance Tracking

#### GET /provenance/{provenance_id}

Get provenance information for a specific analysis.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "type": "ANALYSIS",
    "source_id": "claim_uuid",
    "parent_ids": ["input_uuid", "processing_uuid"],
    "metadata": {
      "analysis_type": "fact_check",
      "confidence": 0.95
    },
    "data_hash": "sha256_hash",
    "confidence_score": 0.95,
    "processing_time_ms": 1250
  }
}
```

#### GET /provenance/chain/{provenance_id}

Get the complete provenance chain for an analysis.

**Response:**
```json
{
  "success": true,
  "data": {
    "chain": [
      {
        "id": "input_uuid",
        "type": "INPUT",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {...}
      },
      {
        "id": "processing_uuid",
        "type": "PROCESSING",
        "timestamp": "2024-01-01T00:00:01Z",
        "metadata": {...}
      }
    ]
  }
}
```

### Human-AI Collaboration

#### POST /collaboration/feedback

Submit user feedback on an analysis.

**Request Body:**
```json
{
  "analysis_id": "uuid",
  "feedback_type": "accuracy",
  "rating": 4,
  "comment": "The analysis was mostly accurate",
  "specific_element": "evidence_quality"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "feedback_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "status": "submitted"
  }
}
```

#### POST /collaboration/override

Submit a user override for an analysis result.

**Request Body:**
```json
{
  "analysis_id": "uuid",
  "override_type": "verdict",
  "original_value": "false",
  "new_value": "true",
  "reason": "Additional evidence provided"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "override_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "status": "applied"
  }
}
```

### Adversarial Testing

#### POST /testing/run-single-test

Run a single adversarial test on provided text.

**Request Body:**
```json
{
  "text": "The Earth is round",
  "attack_types": ["noise_injection", "semantic_perturbation"],
  "parameters": {
    "noise_level": 0.1,
    "replacement_rate": 0.3
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "attack_type": "noise_injection",
        "original_text": "The Earth is round",
        "modified_text": "The Earth is roun",
        "original_verdict": "true",
        "modified_verdict": "true",
        "original_confidence": 0.95,
        "modified_confidence": 0.92,
        "success": false,
        "robustness_score": 0.95
      }
    ],
    "statistics": {
      "total_tests": 1,
      "successful_attacks": 0,
      "attack_success_rate": 0.0,
      "avg_robustness": 0.95
    }
  }
}
```

#### POST /testing/run-synthetic-tests

Run synthetic adversarial tests with generated test cases.

**Request Body:**
```json
{
  "num_cases": 100,
  "run_async": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "test_suite": "Synthetic Adversarial Test Suite",
    "results": [...],
    "statistics": {
      "total_tests": 100,
      "successful_attacks": 15,
      "attack_success_rate": 0.15,
      "avg_robustness": 0.85,
      "overall_robustness_grade": "B"
    }
  }
}
```

### Monitoring

#### GET /monitoring/status

Get overall system status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "health_checks": [
      {
        "service": "failsafe",
        "component": "system",
        "status": "healthy",
        "response_time_ms": 15.2,
        "details": {
          "cpu_percent": 45.2,
          "memory_percent": 67.8,
          "disk_percent": 23.1
        }
      }
    ],
    "active_alerts": [],
    "system_metrics": {
      "cpu_usage": {
        "latest": 45.2,
        "mean": 42.1,
        "max": 78.3
      }
    }
  }
}
```

#### GET /monitoring/metrics

Get system metrics with filtering.

**Query Parameters:**
- `name`: Filter by metric name
- `component`: Filter by component
- `start_time`: Start time filter (ISO 8601)
- `end_time`: End time filter (ISO 8601)
- `limit`: Maximum number of metrics (default: 1000)

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "id": "uuid",
        "name": "system.cpu.usage",
        "value": 45.2,
        "metric_type": "gauge",
        "timestamp": "2024-01-01T00:00:00Z",
        "tags": {},
        "service": "failsafe",
        "component": "system"
      }
    ],
    "count": 1
  }
}
```

#### POST /monitoring/metrics

Record a new metric.

**Request Body:**
```json
{
  "name": "custom.metric",
  "value": 42.5,
  "metric_type": "gauge",
  "component": "custom",
  "tags": {
    "environment": "development"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Metric recorded"
}
```

#### GET /monitoring/alerts

Get system alerts with filtering.

**Query Parameters:**
- `severity`: Filter by severity (low, medium, high, critical)
- `component`: Filter by component
- `resolved`: Filter by resolved status
- `limit`: Maximum number of alerts (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "uuid",
        "title": "Alert: high_cpu_usage",
        "message": "Metric system.cpu.usage is 85.2 gt 80.0",
        "severity": "high",
        "service": "failsafe",
        "component": "system",
        "metric_name": "system.cpu.usage",
        "threshold_value": 80.0,
        "current_value": 85.2,
        "timestamp": "2024-01-01T00:00:00Z",
        "resolved": false
      }
    ],
    "count": 1
  }
}
```

#### POST /monitoring/alerts/rules

Add a new alert rule.

**Request Body:**
```json
{
  "name": "custom_alert",
  "metric_name": "custom.metric",
  "threshold": 100.0,
  "operator": "gt",
  "severity": "medium",
  "component": "custom"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alert rule added"
}
```

#### GET /monitoring/health

Get health check results.

**Query Parameters:**
- `component`: Filter by component
- `status`: Filter by status (healthy, unhealthy, error)
- `limit`: Maximum number of health checks (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "health_checks": [
      {
        "service": "failsafe",
        "component": "system",
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "response_time_ms": 15.2,
        "details": {
          "cpu_percent": 45.2,
          "memory_percent": 67.8,
          "disk_percent": 23.1
        }
      }
    ],
    "count": 1
  }
}
```

#### POST /monitoring/health/{check_name}

Run a specific health check.

**Response:**
```json
{
  "success": true,
  "data": {
    "health_check": {
      "service": "failsafe",
      "component": "system",
      "status": "healthy",
      "timestamp": "2024-01-01T00:00:00Z",
      "response_time_ms": 15.2,
      "details": {
        "cpu_percent": 45.2,
        "memory_percent": 67.8,
        "disk_percent": 23.1
      }
    }
  }
}
```

## Data Models

### ClaimRequest

```json
{
  "text": "string",
  "url": "string (optional)",
  "language": "string (optional)",
  "metadata": "object (optional)"
}
```

### ReportResponse

```json
{
  "claim_id": "string",
  "verdict": "string",
  "confidence": "number",
  "evidence": "array",
  "verification": "object",
  "fallacies": "array",
  "ai_detection": "object (optional)",
  "multilingual": "object (optional)",
  "sag": "object (optional)",
  "provenance": "object (optional)",
  "processing_time_ms": "number (optional)"
}
```

### EvidenceItem

```json
{
  "source": "string",
  "title": "string (optional)",
  "snippet": "string",
  "score": "number (optional)",
  "source_type": "string (optional)",
  "provenance_timestamp": "string (optional)"
}
```

### FallacyItem

```json
{
  "type": "string",
  "explanation": "string (optional)",
  "span": "string (optional)",
  "confidence": "number (optional)",
  "severity": "string (optional)"
}
```

### AIDetectionResult

```json
{
  "is_ai_generated": "boolean",
  "confidence": "number",
  "method": "string",
  "scores": "object (optional)",
  "metadata": "object (optional)"
}
```

### MultilingualData

```json
{
  "detected_language": "string",
  "processing_language": "string",
  "translation_info": "object (optional)",
  "cross_lingual_evidence": "boolean (optional)"
}
```

### SAGData

```json
{
  "analysis_id": "string",
  "language": "string",
  "nodes": "array",
  "edges": "array",
  "rdf_graph": "object",
  "metadata": "object (optional)"
}
```

### ProvenanceData

```json
{
  "analysis_id": "string",
  "timestamp": "string",
  "source": "string",
  "chain": "array"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## Rate Limiting

Rate limiting is applied per IP address:

- **Default**: 100 requests per minute
- **Burst**: 20 requests per 10 seconds
- **Headers**: Rate limit information is included in response headers:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Examples

### Basic Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Earth is flat",
    "language": "en"
  }'
```

### Get System Status

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/status"
```

### Record Custom Metric

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/metrics" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom.requests",
    "value": 1,
    "metric_type": "counter",
    "component": "api"
  }'
```

### Run Adversarial Test

```bash
curl -X POST "http://localhost:8000/api/v1/testing/run-single-test" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Climate change is real",
    "attack_types": ["noise_injection"],
    "parameters": {
      "noise_level": 0.1
    }
  }'
```

## SDKs and Libraries

### Python

```python
import requests

# Basic analysis
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "text": "The Earth is flat",
        "language": "en"
    }
)

result = response.json()
print(f"Verdict: {result['data']['verdict']}")
print(f"Confidence: {result['data']['confidence']}")
```

### JavaScript

```javascript
// Basic analysis
const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: 'The Earth is flat',
    language: 'en'
  })
});

const result = await response.json();
console.log(`Verdict: ${result.data.verdict}`);
console.log(`Confidence: ${result.data.confidence}`);
```

## Changelog

### Version 1.0.0
- Initial API release
- Basic fact-checking functionality
- Provenance tracking
- Human-AI collaboration
- Adversarial testing
- Monitoring and observability

## Support

For API support and questions:
- **Documentation**: [GitHub Wiki](https://github.com/failsafe/failsafe/wiki)
- **Issues**: [GitHub Issues](https://github.com/failsafe/failsafe/issues)
- **Discussions**: [GitHub Discussions](https://github.com/failsafe/failsafe/discussions)






