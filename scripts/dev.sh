#!/bin/bash
# FailSafe Development Script for Linux/macOS
# Provides easy commands for local development without Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default command
COMMAND=${1:-help}

# Helper functions
print_header() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_info() {
    echo -e "${CYAN}$1${NC}"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

install_poetry() {
    print_header "Installing Poetry"
    if check_command poetry; then
        print_success "Poetry is already installed"
        return
    fi
    
    print_warning "Installing Poetry..."
    if command -v curl >/dev/null 2>&1; then
        curl -sSL https://install.python-poetry.org | python3 -
        print_success "Poetry installed successfully"
        print_warning "Please restart your terminal or run: source ~/.bashrc"
    else
        print_error "curl not found. Please install Poetry manually from https://python-poetry.org/docs/#installation"
        exit 1
    fi
}

install_nodejs() {
    print_header "Installing Node.js"
    if check_command node; then
        print_success "Node.js is already installed"
        return
    fi
    
    print_error "Node.js not found. Please install from https://nodejs.org/"
    print_warning "Or use your package manager:"
    print_warning "  Ubuntu/Debian: sudo apt install nodejs npm"
    print_warning "  macOS: brew install node"
    print_warning "  CentOS/RHEL: sudo yum install nodejs npm"
    exit 1
}

setup_backend() {
    print_header "Setting up Backend"
    
    cd backend
    
    # Install Poetry if not available
    if ! check_command poetry; then
        install_poetry
    fi
    
    # Install dependencies
    print_warning "Installing Python dependencies..."
    poetry install
    
    # Create .env file if not exists
    if [ ! -f ".env" ]; then
        print_warning "Creating .env file..."
        cat > .env << EOF
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
EOF
        print_warning ".env file created. Please update with your actual values."
    fi
    
    print_success "Backend setup completed!"
    cd ..
}

setup_frontend() {
    print_header "Setting up Frontend"
    
    cd frontend
    
    # Install Node.js if not available
    if ! check_command node; then
        install_nodejs
    fi
    
    # Install dependencies
    print_warning "Installing Node.js dependencies..."
    npm install
    
    # Create .env file if not exists
    if [ ! -f ".env" ]; then
        print_warning "Creating .env file..."
        cat > .env << EOF
# FailSafe Frontend Environment Variables
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG=true
EOF
    fi
    
    print_success "Frontend setup completed!"
    cd ..
}

start_backend() {
    print_header "Starting Backend Server"
    
    cd backend
    
    if ! check_command poetry; then
        print_error "Poetry not found. Please run './scripts/dev.sh setup' first."
        exit 1
    fi
    
    print_warning "Starting FastAPI server with uvicorn..."
    print_info "Backend will be available at: http://localhost:8000"
    print_info "API docs will be available at: http://localhost:8000/docs"
    print_warning "Press Ctrl+C to stop the server"
    
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend() {
    print_header "Starting Frontend Server"
    
    cd frontend
    
    if ! check_command node; then
        print_error "Node.js not found. Please run './scripts/dev.sh setup' first."
        exit 1
    fi
    
    print_warning "Starting React development server..."
    print_info "Frontend will be available at: http://localhost:3000"
    print_warning "Press Ctrl+C to stop the server"
    
    npm run dev
}

start_all() {
    print_header "Starting All Services"
    
    print_warning "This will start both backend and frontend in separate terminals."
    print_warning "Make sure you have multiple terminals available."
    
    # Start backend in background
    gnome-terminal -- bash -c "cd '$PWD' && ./scripts/dev.sh backend; exec bash" 2>/dev/null || \
    xterm -e "cd '$PWD' && ./scripts/dev.sh backend" 2>/dev/null || \
    osascript -e "tell app \"Terminal\" to do script \"cd '$PWD' && ./scripts/dev.sh backend\"" 2>/dev/null || \
    print_warning "Could not open new terminal. Please run backend manually: ./scripts/dev.sh backend"
    
    # Wait a moment
    sleep 3
    
    # Start frontend in background
    gnome-terminal -- bash -c "cd '$PWD' && ./scripts/dev.sh frontend; exec bash" 2>/dev/null || \
    xterm -e "cd '$PWD' && ./scripts/dev.sh frontend" 2>/dev/null || \
    osascript -e "tell app \"Terminal\" to do script \"cd '$PWD' && ./scripts/dev.sh frontend\"" 2>/dev/null || \
    print_warning "Could not open new terminal. Please run frontend manually: ./scripts/dev.sh frontend"
    
    print_success "Both services started in separate terminals."
    print_info "Backend: http://localhost:8000"
    print_info "Frontend: http://localhost:3000"
}

run_tests() {
    print_header "Running Tests"
    
    # Backend tests
    cd backend
    if check_command poetry; then
        print_warning "Running backend tests..."
        poetry run pytest tests/ -v --tb=short
    fi
    cd ..
    
    # Frontend tests
    cd frontend
    if check_command npm; then
        print_warning "Running frontend tests..."
        npm test -- --watchAll=false
    fi
    cd ..
}

run_lint() {
    print_header "Running Linting"
    
    # Backend linting
    cd backend
    if check_command poetry; then
        print_warning "Running Python linting..."
        poetry run ruff check .
        poetry run ruff format --check .
    fi
    cd ..
    
    # Frontend linting
    cd frontend
    if check_command npm; then
        print_warning "Running TypeScript linting..."
        npm run lint
    fi
    cd ..
}

show_status() {
    print_header "System Status"
    
    # Check Python
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python: $PYTHON_VERSION"
    elif check_command python; then
        PYTHON_VERSION=$(python --version)
        print_success "Python: $PYTHON_VERSION"
    else
        print_error "Python: Not found"
    fi
    
    # Check Poetry
    if check_command poetry; then
        POETRY_VERSION=$(poetry --version)
        print_success "Poetry: $POETRY_VERSION"
    else
        print_error "Poetry: Not found"
    fi
    
    # Check Node.js
    if check_command node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js: $NODE_VERSION"
    else
        print_error "Node.js: Not found"
    fi
    
    # Check npm
    if check_command npm; then
        NPM_VERSION=$(npm --version)
        print_success "npm: $NPM_VERSION"
    else
        print_error "npm: Not found"
    fi
    
    # Check if services are running
    print_info "Service Status:"
    
    if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        print_success "Backend: Running (http://localhost:8000)"
    else
        print_error "Backend: Not running"
    fi
    
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend: Running (http://localhost:3000)"
    else
        print_error "Frontend: Not running"
    fi
}

show_help() {
    print_header "FailSafe Development Commands"
    
    print_warning "Available commands:"
    print_success "  setup     - Setup development environment"
    print_success "  backend   - Start backend server only"
    print_success "  frontend  - Start frontend server only"
    print_success "  start     - Start all services"
    print_success "  test      - Run all tests"
    print_success "  lint      - Run linting"
    print_success "  status    - Show system status"
    print_success "  help      - Show this help"
    
    print_warning "Examples:"
    print_info "  ./scripts/dev.sh setup"
    print_info "  ./scripts/dev.sh backend"
    print_info "  ./scripts/dev.sh frontend"
    print_info "  ./scripts/dev.sh start"
}

# Make script executable
chmod +x "$0"

# Main command dispatcher
case "$COMMAND" in
    setup)
        setup_backend
        setup_frontend
        print_success "Setup completed! You can now run:"
        print_info "  ./scripts/dev.sh backend   # Start backend"
        print_info "  ./scripts/dev.sh frontend  # Start frontend"
        print_info "  ./scripts/dev.sh start     # Start both"
        ;;
    backend) start_backend ;;
    frontend) start_frontend ;;
    start) start_all ;;
    test) run_tests ;;
    lint) run_lint ;;
    status) show_status ;;
    help) show_help ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        ;;
esac