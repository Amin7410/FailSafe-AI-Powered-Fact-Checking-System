# FailSafe Development Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Environment](#development-environment)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Testing](#testing)
7. [Code Style and Standards](#code-style-and-standards)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Contributing](#contributing)

## Getting Started

### Prerequisites

- **Python 3.9+** (recommended: 3.11)
- **Node.js 18+** (recommended: 20)
- **Poetry** (Python dependency management)
- **npm/yarn** (Node.js package management)
- **Git** (version control)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/failsafe/failsafe.git
   cd failsafe
   ```

2. **Setup development environment**
   ```bash
   # Windows
   .\scripts\dev.ps1 setup
   
   # Linux/macOS
   ./scripts/dev.sh setup
   ```

3. **Start development servers**
   ```bash
   # Windows
   .\scripts\dev.ps1 start
   
   # Linux/macOS
   ./scripts/dev.sh start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Project Structure

```
failsafe/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application entry point
│   ├── tests/              # Backend tests
│   ├── pyproject.toml      # Python dependencies
│   └── requirements.txt    # Fallback requirements
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Main React component
│   ├── extension/          # Browser extension
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
├── scripts/                # Development scripts
├── docker-compose.yml      # Docker configuration
└── README.md              # Project overview
```

## Development Environment

### Backend Setup

1. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**
   ```bash
   cd backend
   poetry install
   ```

3. **Activate virtual environment**
   ```bash
   poetry shell
   ```

4. **Run development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=FailSafe

# Database
DATABASE_URL=sqlite:///./failsafe.db

# Redis (optional, falls back to in-memory)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Ethical Configuration
ETHICAL_CONFIG_PATH=./app/core/ethical_config.yaml
```

### Local LLM with Ollama

1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download installer from https://ollama.com/download and run it
```

2. Start the Ollama service

```bash
ollama serve
```

3. Pull a recommended model

```bash
# Choose one based on resources
ollama pull phi3:mini     # small, fast
ollama pull llama3:8b     # larger, better (needs more RAM/VRAM)
```

4. Configure the backend (optional)

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=phi3:mini
```

The backend uses `backend/app/services/llm_client.py` to fetch a concise reasoning string that is appended to `verification.notes` in `SynthesisService`.

### Gemini (Default Cloud LLM Option)

Set environment variables:

```bash
export GEMINI_API_KEY=YOUR_KEY   # hoặc GOOGLE_API_KEY
export GEMINI_MODEL=gemini-1.5-flash
```

Khi có `GEMINI_API_KEY/GOOGLE_API_KEY`, backend sẽ tự chọn Gemini làm LLM mặc định. Nếu không, sẽ fallback sang Ollama.

### OpenAI-Compatible Backend (vLLM / llama.cpp server)

Bạn có thể trỏ tới một endpoint OpenAI-compatible (như vLLM hoặc llama.cpp server):

```bash
export LLM_PROVIDER=openai_compat
export OPENAI_COMPAT_BASE_URL=http://localhost:8001/v1
export OPENAI_COMPAT_MODEL=llama-3-8b-instruct
# optional
export OPENAI_COMPAT_API_KEY=your_local_key
```

Nếu `LLM_PROVIDER` không đặt, hệ thống ưu tiên Gemini (nếu có `GEMINI_API_KEY`), ngược lại dùng Ollama.

### Quantization and High-Performance Backends

For large models, consider quantization and optimized runtimes:

- 4-bit quantization: `bitsandbytes` or `AutoGPTQ` (Python). Reduces VRAM and speeds up inference at minor accuracy cost.
- llama.cpp / llama-cpp-python: CPU/GPU-accelerated inference for GGUF models; low-latency local serving.
- vLLM: High-throughput GPU inference server; excellent for batching and production.

Recommendations:

1) Start with Ollama for simplicity. If latency is high, try llama-cpp-python with a quantized GGUF (`Q4_K_M`).
2) For multi-user throughput, deploy vLLM and point the client at its endpoint.
3) Keep prompts concise. Log average latency and token counts to guide optimization.

## Backend Development

### Architecture Overview

The backend follows a layered architecture:

- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic and orchestration
- **Data Layer**: Models and data access
- **Core Layer**: Configuration and utilities

### Adding New Endpoints

1. **Create endpoint file** in `app/api/v1/endpoints/`
   ```python
   from fastapi import APIRouter
   from pydantic import BaseModel
   
   router = APIRouter(prefix="/example", tags=["example"])
   
   class ExampleRequest(BaseModel):
       text: str
   
   @router.post("/")
   async def create_example(request: ExampleRequest):
       return {"message": "Example created"}
   ```

2. **Register router** in `app/api/v1/router.py`
   ```python
   from .endpoints import example
   
   api_router.include_router(example.router)
   ```

### Adding New Services

1. **Create service file** in `app/services/`
   ```python
   class ExampleService:
       def __init__(self):
           self.logger = logging.getLogger(__name__)
       
       async def process_example(self, text: str) -> dict:
           # Business logic here
           return {"result": "processed"}
   ```

2. **Use service in endpoints**
   ```python
   from ..services.example_service import ExampleService
   
   @router.post("/")
   async def create_example(request: ExampleRequest):
       service = ExampleService()
       result = await service.process_example(request.text)
       return result
   ```

### Database Models

Use Pydantic models for data validation:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExampleModel(BaseModel):
    id: str = Field(..., description="Unique identifier")
    text: str = Field(..., min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = Field(default_factory=dict)
```

### Error Handling

Use FastAPI's HTTPException for consistent error handling:

```python
from fastapi import HTTPException

@router.get("/{item_id}")
async def get_item(item_id: str):
    if not item_id:
        raise HTTPException(status_code=400, detail="Item ID is required")
    
    # ... rest of the logic
```

### Logging

Use structured logging for better observability:

```python
import logging

logger = logging.getLogger(__name__)

# In your service or endpoint
logger.info("Processing request", extra={
    "request_id": request_id,
    "user_id": user_id,
    "action": "analyze_claim"
})
```

## Frontend Development

### Component Structure

Follow this structure for React components:

```
src/components/
├── ComponentName/
│   ├── ComponentName.tsx
│   ├── ComponentName.css
│   ├── ComponentName.test.tsx
│   └── index.ts
```

### TypeScript Types

Define types in `src/types/`:

```typescript
export interface ExampleData {
  id: string;
  text: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface ExampleRequest {
  text: string;
  options?: {
    include_metadata?: boolean;
  };
}
```

### API Services

Create API service functions in `src/services/`:

```typescript
import { ExampleData, ExampleRequest } from '../types/Example';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const exampleService = {
  async createExample(request: ExampleRequest): Promise<ExampleData> {
    const response = await fetch(`${API_BASE_URL}/example`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create example');
    }
    
    return response.json();
  },
};
```

### State Management

Use React hooks for state management:

```typescript
import { useState, useEffect } from 'react';

export const ExampleComponent: React.FC = () => {
  const [data, setData] = useState<ExampleData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await exampleService.createExample({ text: 'example' });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data</div>;
  
  return <div>{data.text}</div>;
};
```

### Styling

Use CSS modules or styled-components for styling:

```css
/* ComponentName.css */
.component {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.component-header {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.component-content {
  color: #666;
  line-height: 1.5;
}
```

## Testing

### Backend Testing

1. **Unit Tests**
   ```python
   import pytest
   from app.services.example_service import ExampleService
   
   @pytest.mark.asyncio
   async def test_example_service():
       service = ExampleService()
       result = await service.process_example("test")
       assert result["result"] == "processed"
   ```

2. **Integration Tests**
   ```python
   from fastapi.testclient import TestClient
   from app.main import app
   
   client = TestClient(app)
   
   def test_example_endpoint():
       response = client.post("/api/v1/example", json={"text": "test"})
       assert response.status_code == 200
       assert response.json()["message"] == "Example created"
   ```

3. **Run Tests**
   ```bash
   cd backend
   poetry run pytest
   ```

### Frontend Testing

1. **Component Tests**
   ```typescript
   import { render, screen } from '@testing-library/react';
   import { ExampleComponent } from './ExampleComponent';
   
   test('renders example component', () => {
     render(<ExampleComponent />);
     expect(screen.getByText('Example')).toBeInTheDocument();
   });
   ```

2. **Run Tests**
   ```bash
   cd frontend
   npm test
   ```

### Adversarial Testing

Run adversarial tests to check system robustness:

```bash
# Run single test
curl -X POST "http://localhost:8000/api/v1/testing/run-single-test" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Climate change is real",
    "attack_types": ["noise_injection"],
    "parameters": {"noise_level": 0.1}
  }'

# Run synthetic test suite
curl -X POST "http://localhost:8000/api/v1/testing/run-synthetic-tests" \
  -H "Content-Type: application/json" \
  -d '{"num_cases": 100}'
```

## Code Style and Standards

### Python

- **Formatting**: Use `black` for code formatting
- **Linting**: Use `ruff` for linting
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Use Google-style docstrings

```python
def example_function(param1: str, param2: int) -> dict:
    """
    Example function with proper type hints and docstring.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary containing the result
    
    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return {"result": f"{param1}_{param2}"}
```

### TypeScript

- **Formatting**: Use `prettier` for code formatting
- **Linting**: Use `eslint` for linting
- **Types**: Use strict TypeScript configuration
- **Comments**: Use JSDoc comments for functions

```typescript
/**
 * Example function with proper JSDoc comments
 * @param param1 - Description of param1
 * @param param2 - Description of param2
 * @returns Promise resolving to the result
 * @throws Error if param1 is empty
 */
async function exampleFunction(
  param1: string,
  param2: number
): Promise<{ result: string }> {
  if (!param1) {
    throw new Error('param1 cannot be empty');
  }
  
  return { result: `${param1}_${param2}` };
}
```

### Git Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

## Debugging

### Backend Debugging

1. **Use debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **Enable debug logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Use FastAPI debug mode**
   ```bash
   uvicorn app.main:app --reload --log-level debug
   ```

### Frontend Debugging

1. **Use React DevTools**
   - Install browser extension
   - Inspect component state and props

2. **Use browser dev tools**
   - Console for JavaScript errors
   - Network tab for API calls
   - Sources tab for breakpoints

3. **Use debugger statement**
   ```typescript
   function exampleFunction() {
     debugger; // Breakpoint here
     // ... rest of the code
   }
   ```

## Performance Optimization

### Backend Optimization

1. **Database queries**
   - Use indexes for frequently queried fields
   - Implement query caching
   - Use connection pooling

2. **API responses**
   - Implement response caching
   - Use pagination for large datasets
   - Compress responses

3. **Async operations**
   - Use async/await for I/O operations
   - Implement background tasks for heavy operations

### Frontend Optimization

1. **Bundle optimization**
   - Use code splitting
   - Implement lazy loading
   - Optimize bundle size

2. **Rendering optimization**
   - Use React.memo for expensive components
   - Implement virtual scrolling for large lists
   - Optimize re-renders

3. **API optimization**
   - Implement request caching
   - Use debouncing for search inputs
   - Implement optimistic updates

## Contributing

### Before Contributing

1. **Read the contributing guidelines**
2. **Check existing issues and PRs**
3. **Fork the repository**
4. **Create a feature branch**

### Development Process

1. **Setup development environment**
2. **Make your changes**
3. **Write tests for your changes**
4. **Run all tests**
5. **Check code style and linting**
6. **Update documentation if needed**
7. **Create a pull request**

### Pull Request Process

1. **Fill out the PR template**
2. **Link related issues**
3. **Request reviews from maintainers**
4. **Address feedback**
5. **Merge after approval**

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact is considered
- [ ] Security implications are reviewed

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Dependencies not installing**
   ```bash
   # Clear cache and reinstall
   poetry cache clear --all pypi
   poetry install
   ```

3. **Frontend build errors**
   ```bash
   # Clear node modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Database connection issues**
   - Check database URL in environment variables
   - Ensure database is running
   - Check network connectivity

### Getting Help

- **Documentation**: Check this guide and API reference
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our Discord server for real-time help

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Vite Documentation](https://vitejs.dev/guide/)






