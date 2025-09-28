# FailSafe Development Script for Windows PowerShell
# Provides easy commands for local development without Docker

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-ColorOutput "`n=== $Title ===" $Cyan
}

function Check-Command {
    param([string]$CommandName)
    try {
        Get-Command $CommandName -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Install-Poetry {
    Write-Header "Installing Poetry"
    if (Check-Command "poetry") {
        Write-ColorOutput "Poetry is already installed" $Green
        return
    }
    
    Write-ColorOutput "Installing Poetry..." $Yellow
    try {
        Invoke-Expression (Invoke-WebRequest -Uri "https://install.python-poetry.org" -UseBasicParsing).Content
        Write-ColorOutput "Poetry installed successfully" $Green
        Write-ColorOutput "Please restart your terminal or run: refreshenv" $Yellow
    }
    catch {
        Write-ColorOutput "Failed to install Poetry. Please install manually from https://python-poetry.org/docs/#installation" $Red
        exit 1
    }
}

function Install-NodeJS {
    Write-Header "Installing Node.js"
    if (Check-Command "node") {
        Write-ColorOutput "Node.js is already installed" $Green
        return
    }
    
    Write-ColorOutput "Node.js not found. Please install from https://nodejs.org/" $Red
    Write-ColorOutput "Or use chocolatey: choco install nodejs" $Yellow
    exit 1
}

function Setup-Backend {
    Write-Header "Setting up Backend"
    
    Push-Location "backend"
    
    try {
        # Install Poetry if not available
        if (-not (Check-Command "poetry")) {
            Install-Poetry
        }
        
        # Install dependencies
        Write-ColorOutput "Installing Python dependencies..." $Yellow
        poetry install
        
        # Create .env file if not exists
        if (-not (Test-Path ".env")) {
            Write-ColorOutput "Creating .env file..." $Yellow
            @"
# FailSafe Backend Environment Variables
PYTHONPATH=/app
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./failsafe.db
REDIS_URL=redis://localhost:6379

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# External APIs
PUBMED_API_KEY=your_pubmed_key_here
HUGGINGFACE_TOKEN=your_hf_token_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Cache
CACHE_TTL=300
CACHE_MAX_ENTRIES=1000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_BURST=20
"@ | Out-File -FilePath ".env" -Encoding UTF8
            Write-ColorOutput ".env file created. Please update with your actual values." $Yellow
        }
        
        Write-ColorOutput "Backend setup completed!" $Green
    }
    finally {
        Pop-Location
    }
}

function Setup-Frontend {
    Write-Header "Setting up Frontend"
    
    Push-Location "frontend"
    
    try {
        # Install Node.js if not available
        if (-not (Check-Command "node")) {
            Install-NodeJS
        }
        
        # Install dependencies
        Write-ColorOutput "Installing Node.js dependencies..." $Yellow
        npm install
        
        # Create .env file if not exists
        if (-not (Test-Path ".env")) {
            Write-ColorOutput "Creating .env file..." $Yellow
            @"
# FailSafe Frontend Environment Variables
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG=true
"@ | Out-File -FilePath ".env" -Encoding UTF8
        }
        
        Write-ColorOutput "Frontend setup completed!" $Green
    }
    finally {
        Pop-Location
    }
}

function Start-Backend {
    Write-Header "Starting Backend Server"
    
    Push-Location "backend"
    
    try {
        if (-not (Check-Command "poetry")) {
            Write-ColorOutput "Poetry not found. Please run 'dev setup' first." $Red
            exit 1
        }
        
        Write-ColorOutput "Starting FastAPI server with uvicorn..." $Yellow
        Write-ColorOutput "Backend will be available at: http://localhost:8000" $Cyan
        Write-ColorOutput "API docs will be available at: http://localhost:8000/docs" $Cyan
        Write-ColorOutput "Press Ctrl+C to stop the server" $Yellow
        
        poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    finally {
        Pop-Location
    }
}

function Start-Frontend {
    Write-Header "Starting Frontend Server"
    
    Push-Location "frontend"
    
    try {
        if (-not (Check-Command "node")) {
            Write-ColorOutput "Node.js not found. Please run 'dev setup' first." $Red
            exit 1
        }
        
        Write-ColorOutput "Starting React development server..." $Yellow
        Write-ColorOutput "Frontend will be available at: http://localhost:3000" $Cyan
        Write-ColorOutput "Press Ctrl+C to stop the server" $Yellow
        
        npm run dev
    }
    finally {
        Pop-Location
    }
}

function Start-All {
    Write-Header "Starting All Services"
    
    Write-ColorOutput "This will start both backend and frontend in separate windows." $Yellow
    Write-ColorOutput "Make sure you have both terminals available." $Yellow
    
    # Start backend in new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\scripts\dev.ps1 backend"
    
    # Wait a moment
    Start-Sleep -Seconds 3
    
    # Start frontend in new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\scripts\dev.ps1 frontend"
    
    Write-ColorOutput "Both services started in separate windows." $Green
    Write-ColorOutput "Backend: http://localhost:8000" $Cyan
    Write-ColorOutput "Frontend: http://localhost:3000" $Cyan
}

function Run-Tests {
    Write-Header "Running Tests"
    
    Push-Location "backend"
    
    try {
        if (-not (Check-Command "poetry")) {
            Write-ColorOutput "Poetry not found. Please run 'dev setup' first." $Red
            exit 1
        }
        
        Write-ColorOutput "Running backend tests..." $Yellow
        poetry run pytest tests/ -v --tb=short
        
        Write-ColorOutput "Running frontend tests..." $Yellow
        Pop-Location
        Push-Location "frontend"
        npm test -- --watchAll=false
    }
    finally {
        Pop-Location
    }
}

function Run-Lint {
    Write-Header "Running Linting"
    
    # Backend linting
    Push-Location "backend"
    try {
        if (Check-Command "poetry") {
            Write-ColorOutput "Running Python linting..." $Yellow
            poetry run ruff check .
            poetry run ruff format --check .
        }
    }
    finally {
        Pop-Location
    }
    
    # Frontend linting
    Push-Location "frontend"
    try {
        if (Check-Command "npm") {
            Write-ColorOutput "Running TypeScript linting..." $Yellow
            npm run lint
        }
    }
    finally {
        Pop-Location
    }
}

function Show-Status {
    Write-Header "System Status"
    
    # Check Python
    if (Check-Command "python") {
        $pythonVersion = python --version
        Write-ColorOutput "Python: $pythonVersion" $Green
    } else {
        Write-ColorOutput "Python: Not found" $Red
    }
    
    # Check Poetry
    if (Check-Command "poetry") {
        $poetryVersion = poetry --version
        Write-ColorOutput "Poetry: $poetryVersion" $Green
    } else {
        Write-ColorOutput "Poetry: Not found" $Red
    }
    
    # Check Node.js
    if (Check-Command "node") {
        $nodeVersion = node --version
        Write-ColorOutput "Node.js: $nodeVersion" $Green
    } else {
        Write-ColorOutput "Node.js: Not found" $Red
    }
    
    # Check npm
    if (Check-Command "npm") {
        $npmVersion = npm --version
        Write-ColorOutput "npm: $npmVersion" $Green
    } else {
        Write-ColorOutput "npm: Not found" $Red
    }
    
    # Check if services are running
    Write-ColorOutput "`nService Status:" $Cyan
    
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 2 -ErrorAction Stop
        Write-ColorOutput "Backend: Running (http://localhost:8000)" $Green
    }
    catch {
        Write-ColorOutput "Backend: Not running" $Red
    }
    
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
        Write-ColorOutput "Frontend: Running (http://localhost:3000)" $Green
    }
    catch {
        Write-ColorOutput "Frontend: Not running" $Red
    }
}

function Show-Help {
    Write-Header "FailSafe Development Commands"
    
    Write-ColorOutput "Available commands:" $Yellow
    Write-ColorOutput "  setup     - Setup development environment" $Green
    Write-ColorOutput "  backend   - Start backend server only" $Green
    Write-ColorOutput "  frontend  - Start frontend server only" $Green
    Write-ColorOutput "  start     - Start all services" $Green
    Write-ColorOutput "  test      - Run all tests" $Green
    Write-ColorOutput "  lint      - Run linting" $Green
    Write-ColorOutput "  status    - Show system status" $Green
    Write-ColorOutput "  help      - Show this help" $Green
    
    Write-ColorOutput "`nExamples:" $Yellow
    Write-ColorOutput "  .\scripts\dev.ps1 setup" $Cyan
    Write-ColorOutput "  .\scripts\dev.ps1 backend" $Cyan
    Write-ColorOutput "  .\scripts\dev.ps1 frontend" $Cyan
    Write-ColorOutput "  .\scripts\dev.ps1 start" $Cyan
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "setup" {
        Setup-Backend
        Setup-Frontend
        Write-ColorOutput "`nSetup completed! You can now run:" $Green
        Write-ColorOutput "  .\scripts\dev.ps1 backend   # Start backend" $Cyan
        Write-ColorOutput "  .\scripts\dev.ps1 frontend  # Start frontend" $Cyan
        Write-ColorOutput "  .\scripts\dev.ps1 start     # Start both" $Cyan
    }
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "start" { Start-All }
    "test" { Run-Tests }
    "lint" { Run-Lint }
    "status" { Show-Status }
    "help" { Show-Help }
    default {
        Write-ColorOutput "Unknown command: $Command" $Red
        Show-Help
    }
}