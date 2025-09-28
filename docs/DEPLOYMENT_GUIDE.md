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

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Monitoring
ENABLE_MONITORING=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_ENDPOINT=/health
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

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     failsafe-backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://postgres:password@db:5432/failsafe
         - REDIS_URL=redis://redis:6379
       depends_on:
         - db
         - redis
       volumes:
         - ./backend:/app
         - ./data:/app/data
   
     failsafe-frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - REACT_APP_API_URL=http://localhost:8000
       depends_on:
         - failsafe-backend
   
     db:
       image: postgres:15
       environment:
         - POSTGRES_DB=failsafe
         - POSTGRES_USER=postgres
         - POSTGRES_PASSWORD=password
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
   
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
       depends_on:
         - failsafe-frontend
         - failsafe-backend
   
   volumes:
     postgres_data:
     redis_data:
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Check service status**
   ```bash
   docker-compose ps
   ```

4. **View logs**
   ```bash
   docker-compose logs -f failsafe-backend
   ```

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

### Nginx Configuration

Create `/etc/nginx/sites-available/failsafe`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/certs/failsafe.crt;
    ssl_certificate_key /etc/ssl/private/failsafe.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Frontend
    location / {
        root /var/www/failsafe/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Metrics (restrict access)
    location /metrics {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://127.0.0.1:8000/metrics;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/failsafe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

#### Using Let's Encrypt

1. **Install Certbot**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Obtain certificate**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Auto-renewal**
   ```bash
   sudo crontab -e
   ```

   Add this line:
   ```
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Systemd Service

Create `/etc/systemd/system/failsafe.service`:

```ini
[Unit]
Description=FailSafe API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=failsafe
Group=failsafe
WorkingDirectory=/opt/failsafe
Environment=PATH=/opt/failsafe/venv/bin
ExecStart=/opt/failsafe/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable failsafe
sudo systemctl start failsafe
```

## Monitoring and Maintenance

### Health Checks

#### Application Health Check

```bash
curl -f http://localhost:8000/health
```

#### Database Health Check

```bash
psql -h localhost -U failsafe_user -d failsafe -c "SELECT 1;"
```

#### Redis Health Check

```bash
redis-cli ping
```

### Log Management

#### Log Rotation

Create `/etc/logrotate.d/failsafe`:

```
/var/log/failsafe/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 failsafe failsafe
    postrotate
        systemctl reload failsafe
    endscript
}
```

#### Log Monitoring

```bash
# Monitor logs in real-time
tail -f /var/log/failsafe/app.log

# Search for errors
grep -i error /var/log/failsafe/app.log

# Monitor API requests
grep "POST /api/v1/analyze" /var/log/failsafe/app.log
```

### Performance Monitoring

#### System Metrics

```bash
# CPU usage
top -p $(pgrep -f uvicorn)

# Memory usage
free -h

# Disk usage
df -h

# Network connections
netstat -tulpn | grep :8000
```

#### Application Metrics

```bash
# API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Database connections
psql -h localhost -U failsafe_user -d failsafe -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
redis-cli info memory
```

### Backup and Recovery

#### Database Backup

```bash
# Create backup
pg_dump -h localhost -U failsafe_user -d failsafe > failsafe_backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -h localhost -U failsafe_user -d failsafe < failsafe_backup_20240101_120000.sql
```

#### Application Backup

```bash
# Backup application files
tar -czf failsafe_app_$(date +%Y%m%d_%H%M%S).tar.gz /opt/failsafe

# Backup configuration
tar -czf failsafe_config_$(date +%Y%m%d_%H%M%S).tar.gz /etc/nginx/sites-available/failsafe /etc/systemd/system/failsafe.service
```

### Updates and Maintenance

#### Application Updates

1. **Stop service**
   ```bash
   sudo systemctl stop failsafe
   ```

2. **Backup current version**
   ```bash
   cp -r /opt/failsafe /opt/failsafe_backup_$(date +%Y%m%d)
   ```

3. **Update code**
   ```bash
   cd /opt/failsafe
   git pull origin main
   ```

4. **Update dependencies**
   ```bash
   poetry install
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start service**
   ```bash
   sudo systemctl start failsafe
   ```

#### System Updates

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade

# Update Python packages
poetry update

# Update Node.js packages
npm update
```

## Security Considerations

### Network Security

- **Firewall**: Configure UFW or iptables to restrict access
- **SSL/TLS**: Use HTTPS for all communications
- **VPN**: Use VPN for administrative access
- **DDoS Protection**: Implement rate limiting and DDoS protection

### Application Security

- **Input Validation**: Validate all user inputs
- **SQL Injection**: Use parameterized queries
- **XSS Protection**: Sanitize user inputs
- **CSRF Protection**: Implement CSRF tokens
- **Authentication**: Use strong authentication mechanisms

### Data Security

- **Encryption**: Encrypt sensitive data at rest and in transit
- **Access Control**: Implement proper access controls
- **Audit Logging**: Log all security-relevant events
- **Data Retention**: Implement data retention policies

### Monitoring Security

- **Intrusion Detection**: Monitor for suspicious activities
- **Log Analysis**: Analyze logs for security events
- **Vulnerability Scanning**: Regular vulnerability assessments
- **Penetration Testing**: Periodic security testing

## Troubleshooting

### Common Issues

#### Service Won't Start

1. **Check logs**
   ```bash
   sudo journalctl -u failsafe -f
   ```

2. **Check configuration**
   ```bash
   sudo systemctl status failsafe
   ```

3. **Check dependencies**
   ```bash
   sudo systemctl status postgresql redis
   ```

#### Database Connection Issues

1. **Check database status**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Check connection string**
   ```bash
   echo $DATABASE_URL
   ```

3. **Test connection**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

#### High Memory Usage

1. **Check memory usage**
   ```bash
   free -h
   top -p $(pgrep -f uvicorn)
   ```

2. **Check for memory leaks**
   ```bash
   ps aux | grep uvicorn
   ```

3. **Restart service**
   ```bash
   sudo systemctl restart failsafe
   ```

#### Slow Response Times

1. **Check CPU usage**
   ```bash
   top -p $(pgrep -f uvicorn)
   ```

2. **Check database performance**
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"
   ```

3. **Check Redis performance**
   ```bash
   redis-cli info stats
   ```

### Debugging Tools

#### Application Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
sudo systemctl restart failsafe

# Check debug logs
sudo journalctl -u failsafe -f | grep DEBUG
```

#### Database Debugging

```bash
# Enable query logging
sudo nano /etc/postgresql/15/main/postgresql.conf
# Set log_statement = 'all'
sudo systemctl restart postgresql
```

#### Network Debugging

```bash
# Check network connections
netstat -tulpn | grep :8000

# Test API endpoints
curl -v http://localhost:8000/health

# Check SSL certificate
openssl s_client -connect yourdomain.com:443
```

### Performance Tuning

#### Database Tuning

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'your_table';
```

#### Application Tuning

```python
# Increase worker processes
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Enable gzip compression
# Add to FastAPI app
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### System Tuning

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying FailSafe in various environments. Choose the deployment method that best fits your needs and follow the security and monitoring recommendations for a production-ready deployment.

For additional support and troubleshooting, refer to the documentation or contact the FailSafe team.






