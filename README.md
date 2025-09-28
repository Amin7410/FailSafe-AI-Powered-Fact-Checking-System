# 🛡️ FailSafe - AI-Powered Fact-Checking System

FailSafe is an advanced AI-powered system for fact-checking and misinformation analysis, designed to help users verify claims and detect logical fallacies in real-time.

## ✨ Features

### 🔍 **Core Analysis**
- **Fact-Checking**: Comprehensive verification of claims using multiple sources
- **Logical Fallacy Detection**: Advanced detection of 10+ fallacy types
- **AI-Generated Content Detection**: Multi-signal approach to identify AI-generated text
- **Multilingual Support**: Support for 10+ languages with automatic detection

### 🧠 **Advanced AI**
- **Structured Argument Graph (SAG)**: RDF/OWL compliant knowledge representation
- **Enhanced Anti-Hallucination**: Multi-agent cross-checking and self-reflection
- **Confidence Calibration**: TruthfulQA-based confidence scoring
- **Cross-lingual Knowledge Graph**: Concept mapping across languages

### ⚡ **Performance & Monitoring**
- **Intelligent Caching**: Multi-tier caching system (memory + disk)
- **Real-time Monitoring**: Performance metrics and health checks
- **Optimization Suggestions**: AI-powered performance recommendations
- **Scalable Architecture**: Designed for high-throughput production

### 🔒 **Security & Ethics**
- **Rate Limiting**: Configurable limits to prevent abuse
- **Privacy Protection**: GDPR-compliant data handling
- **Bias Detection**: Built-in bias detection and mitigation
- **Transparency**: Explainable AI with detailed reasoning

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker (optional)

### Development Setup

#### Option 1: Using Development Scripts (Recommended)

**Windows (PowerShell):**
```powershell
# Setup development environment
.\scripts\dev.ps1 setup

# Run backend
.\scripts\dev.ps1 backend

# Run frontend (in another terminal)
.\scripts\dev.ps1 frontend

# Run tests
.\scripts\dev.ps1 test

# Run with Docker
.\scripts\dev.ps1 docker
```

**Linux/macOS (Bash):**
```bash
# Setup development environment
./scripts/dev.sh setup

# Run backend
./scripts/dev.sh backend

# Run frontend (in another terminal)
./scripts/dev.sh frontend

# Run tests
./scripts/dev.sh test

# Run with Docker
./scripts/dev.sh docker
```

#### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

### Docker Setup

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 API Documentation

### Core Endpoints

- **`POST /api/v1/analyze`** - Main analysis endpoint
- **`GET /api/v1/health`** - Health check
- **`GET /api/v1/monitor/status`** - System status
- **`GET /api/v1/monitor/performance`** - Performance metrics
- **`GET /api/v1/monitor/cache`** - Cache statistics

### Example Usage

```python
import requests

# Analyze a claim
response = requests.post("http://localhost:8000/api/v1/analyze", json={
    "text": "Climate change is a hoax",
    "language": "en",
    "metadata": {"source": "social_media"}
})

result = response.json()
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']}")
print(f"Fallacies: {len(result['fallacies'])}")
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Custom Docs**: http://localhost:8000/api/v1/docs/

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Core configuration
│   ├── models/               # Pydantic models
│   └── services/             # Business logic
│       ├── ai_detection_service.py
│       ├── cache_service.py
│       ├── fallacy_detector.py
│       ├── multilingual_service.py
│       ├── performance_service.py
│       └── ...
├── tests/                    # Unit tests
├── Dockerfile
└── requirements.txt
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/           # React components
│   ├── services/             # API services
│   ├── types/                # TypeScript types
│   └── App.tsx
├── Dockerfile
└── package.json
```

## 🧪 Testing

### Run All Tests
```bash
# Using development script
.\scripts\dev.ps1 test

# Or manually
cd backend
python -m pytest tests/ -v
```

### Test Coverage
- **IngestionService**: 8/8 tests ✅
- **FallacyDetector**: 14/14 tests ✅
- **CacheService**: 16/16 tests ✅
- **PerformanceService**: 17/17 tests ✅
- **Total**: 55/55 tests (100% pass rate)

## 📊 Monitoring & Performance

### Health Checks
```bash
# System health
curl http://localhost:8000/api/v1/health

# Performance metrics
curl http://localhost:8000/api/v1/monitor/performance

# Cache statistics
curl http://localhost:8000/api/v1/monitor/cache

# Optimization suggestions
curl http://localhost:8000/api/v1/monitor/optimization
```

### Performance Features
- **Response Time Tracking**: Monitor API response times
- **Memory Usage**: Track memory consumption
- **CPU Monitoring**: Real-time CPU usage
- **Cache Hit/Miss Ratios**: Optimize caching performance
- **Model Inference Timing**: Monitor AI model performance

## 🌐 Multilingual Support

Supported languages:
- English (en)
- Vietnamese (vi)
- Spanish (es)
- French (fr)
- German (de)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Arabic (ar)
- Hindi (hi)

## 🔧 Configuration

### Environment Variables
```bash
# Backend
PYTHONPATH=/app
ENVIRONMENT=production

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Ethical Configuration
Edit `backend/app/core/ethical_config.yaml` to configure:
- Bias thresholds
- Rate limits
- Privacy settings
- Cache configuration
- Performance monitoring

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling
- **Horizontal Scaling**: Use multiple backend instances
- **Load Balancing**: Configure nginx for load distribution
- **Caching**: Redis for distributed caching
- **Database**: PostgreSQL for persistent storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive tests
- Update documentation
- Follow semantic versioning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hugging Face Transformers** for AI models
- **spaCy** for NLP processing
- **FastAPI** for the web framework
- **React** for the frontend framework
- **Docker** for containerization

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8000/api/v1/docs/)
- **Issues**: [GitHub Issues]()
- **Discussions**: [GitHub Discussions]()

---

**FailSafe** - Making the internet a more truthful place, one claim at a time. 🛡️✨