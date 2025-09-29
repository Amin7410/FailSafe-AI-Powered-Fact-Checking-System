# FailSafe Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Production Configuration](#production-configuration)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

## Overview

This guide covers different deployment options for FailSafe, from local development to production cloud deployments. Choose the deployment method that best fits your needs and infrastructure.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB available space
- **OS**: Linux, macOS, or Windows 10+

#### Recommended Requirements
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8+ GB
- **Storage**: 50+ GB available space
- **OS**: Ubuntu 20.04+ or CentOS 8+

#### Production Requirements
- **CPU**: 8+ cores, 3.5+ GHz
- **RAM**: 16+ GB
- **Storage**: 100+ GB SSD
- **OS**: Ubuntu 22.04 LTS or RHEL 8+

### Software Dependencies

- **Python 3.9+** (recommended: 3.11)
- **Node.js 18+** (recommended: 20)
- **Docker** (for containerized deployment)
- **Docker Compose** (for multi-container deployment)
- **Git** (for source code management)

### Optional Dependencies

- **Redis** (for caching and session storage)
- **PostgreSQL** (for production database)
- **Nginx** (for reverse proxy and load balancing)
- **Certbot** (for SSL certificate management)

## Local Development

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

### Manual Setup

#### Backend Setup

1. **Install Python dependencies**
   ```bash
   cd backend
   poetry install
   ```

2. **Activate virtual environment**
   ```bash
   poetry shell
   ```

3. **Run database migrations** (if using database)
   ```bash
   alembic upgrade head
   ```

4. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=FailSafe
VERSION=1.0.0

# Database
DATABASE_URL=sqlite:///./failsafe.db
# For PostgreSQL: postgresql://user:password@localhost/failsafe

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Ethical Configuration
ETHICAL_CONFIG_PATH=./app/core/ethical_config.yaml

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS and API Keys
ALLOWED_ORIGINS=http://localhost:3000
FAILSAFE_API_KEYS=dev_key_1,dev_key_2
```

## Docker Deployment

### Single Container

1. **Build the image**
   ```bash
   docker build -t failsafe:latest .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name failsafe \
     -p 8000:8000 \
     -e DATABASE_URL=sqlite:///./failsafe.db \
     failsafe:latest
   ```

### Multi-Container with Docker Compose

The provided `docker-compose.yml` now includes backend, frontend, Redis, Postgres, and Neo4j with healthchecks. After `docker compose up -d`, access:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Neo4j Browser: http://localhost:7474 (default auth neo4j/neo4jpass)

> Tip: Change default passwords for Postgres and Neo4j in production.

### Nginx Reverse Proxy

See `nginx/nginx.conf` (example). Map `/` to the frontend and `/api/` to the backend. Ensure SSL termination and security headers are configured as in the sample earlier in this guide.

### Dockerfile Examples

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 failsafe && \
    chown -R failsafe:failsafe /app
USER failsafe

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS cluster**
   ```bash
   aws ecs create-cluster --cluster-name failsafe-cluster
   ```

2. **Create task definition**
   ```json
   {
     "family": "failsafe-task",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "failsafe-backend",
         "image": "your-account.dkr.ecr.region.amazonaws.com/failsafe:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://user:password@rds-endpoint:5432/failsafe"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/failsafe",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

3. **Create service**
   ```bash
   aws ecs create-service \
     --cluster failsafe-cluster \
     --service-name failsafe-service \
     --task-definition failsafe-task \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using AWS App Runner

1. **Create apprunner.yaml**
   ```yaml
   version: 1.0
   runtime: python3
   build:
     commands:
       build:
         - pip install -r requirements.txt
   run:
     runtime-version: 3.11
     command: uvicorn app.main:app --host 0.0.0.0 --port 8000
     network:
       port: 8000
       env: PORT
     env:
       - name: DATABASE_URL
         value: postgresql://user:password@rds-endpoint:5432/failsafe
   ```

2. **Deploy using AWS CLI**
   ```bash
   aws apprunner create-service \
     --service-name failsafe-service \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "your-account.dkr.ecr.region.amazonaws.com/failsafe:latest",
         "ImageConfiguration": {
           "Port": "8000"
         }
       }
     }'
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/failsafe
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy failsafe \
     --image gcr.io/PROJECT_ID/failsafe \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL=postgresql://user:password@cloudsql-instance:5432/failsafe
   ```

#### Using GKE

1. **Create cluster**
   ```bash
   gcloud container clusters create failsafe-cluster \
     --num-nodes 3 \
     --machine-type e2-medium \
     --zone us-central1-a
   ```

2. **Deploy application**
   ```bash
   kubectl apply -f k8s/
   ```

### Azure

#### Using Container Instances

1. **Create resource group**
   ```bash
   az group create --name failsafe-rg --location eastus
   ```

2. **Deploy container**
   ```bash
   az container create \
     --resource-group failsafe-rg \
     --name failsafe-container \
     --image your-registry.azurecr.io/failsafe:latest \
     --dns-name-label failsafe-app \
     --ports 8000 \
     --environment-variables DATABASE_URL=postgresql://user:password@server:5432/failsafe
   ```

#### Using Azure Container Apps

1. **Create container app environment**
   ```bash
   az containerapp env create \
     --name failsafe-env \
     --resource-group failsafe-rg \
     --location eastus
   ```

2. **Deploy container app**
   ```bash
   az containerapp create \
     --name failsafe-app \
     --resource-group failsafe-rg \
     --environment failsafe-env \
     --image your-registry.azurecr.io/failsafe:latest \
     --target-port 8000 \
     --ingress external
   ```

## Production Configuration

### Environment Variables

Create a production `.env` file:

```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=FailSafe
VERSION=1.0.0
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/failsafe
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://redis-host:6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/failsafe/app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
RATE_LIMIT_BURST=100

# Security
SECRET_KEY=your-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# SSL
SSL_CERT_PATH=/etc/ssl/certs/failsafe.crt
SSL_KEY_PATH=/etc/ssl/private/failsafe.key

# Monitoring
ENABLE_MONITORING=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_ENDPOINT=/health
PROMETHEUS_ENDPOINT=/prometheus

# External Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

### Database Configuration

#### PostgreSQL Setup

1. **Install PostgreSQL**
   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **Create database and user**
   ```sql
   CREATE DATABASE failsafe;
   CREATE USER failsafe_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE failsafe TO failsafe_user;
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

#### Redis Setup

1. **Install Redis**
   ```bash
   sudo apt-get install redis-server
   ```

2. **Configure Redis**
   ```bash
   sudo nano /etc/redis/redis.conf
   ```

   Add these settings:
   ```
   requirepass your_redis_password
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   ```

3. **Restart Redis**
   ```bash
   sudo systemctl restart redis-server
   ```