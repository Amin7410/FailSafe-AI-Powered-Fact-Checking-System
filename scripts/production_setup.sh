#!/bin/bash

# FailSafe Production Setup Script
# This script sets up FailSafe for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="failsafe"
PROJECT_DIR="/opt/failsafe"
SERVICE_USER="failsafe"
SERVICE_GROUP="failsafe"
BACKUP_DIR="/var/backups/failsafe"
LOG_DIR="/var/log/failsafe"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        nodejs \
        npm \
        nginx \
        postgresql \
        postgresql-contrib \
        redis-server \
        certbot \
        python3-certbot-nginx \
        ufw \
        fail2ban \
        htop \
        curl \
        wget \
        git \
        unzip \
        tar \
        gzip \
        build-essential \
        libssl-dev \
        libffi-dev \
        libpq-dev
}

create_user() {
    log_info "Creating service user..."
    
    # Create user and group
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$PROJECT_DIR" -m "$SERVICE_USER"
        usermod -aG "$SERVICE_USER" "$SERVICE_USER"
    fi
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create project directory
    mkdir -p "$PROJECT_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$BACKUP_DIR"
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    
    # Create nginx directories
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
}

setup_database() {
    log_info "Setting up PostgreSQL database..."
    
    # Start PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE failsafe;
CREATE USER failsafe_user WITH PASSWORD 'secure_password_$(date +%s)';
GRANT ALL PRIVILEGES ON DATABASE failsafe TO failsafe_user;
ALTER USER failsafe_user CREATEDB;
EOF
    
    # Configure PostgreSQL
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
    PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
    
    # Update PostgreSQL configuration
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" "$PG_CONFIG"
    sed -i "s/#max_connections = 100/max_connections = 200/" "$PG_CONFIG"
    sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/" "$PG_CONFIG"
    
    # Restart PostgreSQL
    systemctl restart postgresql
}

setup_redis() {
    log_info "Setting up Redis..."
    
    # Start Redis
    systemctl start redis-server
    systemctl enable redis-server
    
    # Configure Redis
    REDIS_CONFIG="/etc/redis/redis.conf"
    
    # Set password
    REDIS_PASSWORD="redis_password_$(date +%s)"
    echo "requirepass $REDIS_PASSWORD" >> "$REDIS_CONFIG"
    
    # Configure memory policy
    echo "maxmemory 2gb" >> "$REDIS_CONFIG"
    echo "maxmemory-policy allkeys-lru" >> "$REDIS_CONFIG"
    
    # Restart Redis
    systemctl restart redis-server
    
    # Save password for later use
    echo "REDIS_PASSWORD=$REDIS_PASSWORD" > /opt/failsafe/redis_password
    chown "$SERVICE_USER:$SERVICE_GROUP" /opt/failsafe/redis_password
    chmod 600 /opt/failsafe/redis_password
}

setup_nginx() {
    log_info "Setting up Nginx..."
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/failsafe << 'EOF'
server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
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
        root /opt/failsafe/frontend/dist;
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
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/failsafe /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    # Start Nginx
    systemctl start nginx
    systemctl enable nginx
}

setup_firewall() {
    log_info "Setting up firewall..."
    
    # Enable UFW
    ufw --force enable
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow internal communication
    ufw allow from 127.0.0.1 to any port 8000
    ufw allow from 127.0.0.1 to any port 5432
    ufw allow from 127.0.0.1 to any port 6379
    
    # Show status
    ufw status
}

setup_fail2ban() {
    log_info "Setting up Fail2ban..."
    
    # Create Fail2ban configuration
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[postgresql]
enabled = true
port = 5432
logpath = /var/log/postgresql/postgresql-*.log
maxretry = 3
EOF

    # Start Fail2ban
    systemctl start fail2ban
    systemctl enable fail2ban
}

setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    # Create systemd service file
    cat > /etc/systemd/system/failsafe.service << 'EOF'
[Unit]
Description=FailSafe API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=failsafe
Group=failsafe
WorkingDirectory=/opt/failsafe
Environment=PATH=/opt/failsafe/venv/bin
Environment=PYTHONPATH=/opt/failsafe
ExecStart=/opt/failsafe/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=failsafe

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    systemctl enable failsafe
}

setup_cron_jobs() {
    log_info "Setting up cron jobs..."
    
    # Create cron job for backups
    cat > /etc/cron.d/failsafe-backup << 'EOF'
# FailSafe Backup Schedule
0 2 * * * root /opt/failsafe/scripts/backup.sh full
0 */6 * * * root /opt/failsafe/scripts/backup.sh database
0 1 * * 0 root /opt/failsafe/scripts/backup.sh config
0 3 * * * root /opt/failsafe/scripts/backup.sh cleanup
EOF

    # Create backup script
    cat > /opt/failsafe/scripts/backup.sh << 'EOF'
#!/bin/bash
# FailSafe Backup Script

BACKUP_TYPE=$1
API_URL="http://localhost:8000/api/v1/backup"

case $BACKUP_TYPE in
    "full")
        curl -X POST "$API_URL/create" -H "Content-Type: application/json" -d '{"backup_type": "full"}'
        ;;
    "database")
        curl -X POST "$API_URL/create" -H "Content-Type: application/json" -d '{"backup_type": "database"}'
        ;;
    "config")
        curl -X POST "$API_URL/create" -H "Content-Type: application/json" -d '{"backup_type": "configuration"}'
        ;;
    "cleanup")
        curl -X POST "$API_URL/cleanup"
        ;;
    *)
        echo "Invalid backup type: $BACKUP_TYPE"
        exit 1
        ;;
esac
EOF

    chmod +x /opt/failsafe/scripts/backup.sh
    chown -R "$SERVICE_USER:$SERVICE_GROUP" /opt/failsafe/scripts
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/failsafe << 'EOF'
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
EOF

    # Create monitoring script
    cat > /opt/failsafe/scripts/monitor.sh << 'EOF'
#!/bin/bash
# FailSafe Monitoring Script

LOG_FILE="/var/log/failsafe/monitor.log"
API_URL="http://localhost:8000/api/v1/monitoring/status"

# Check API health
if curl -f -s "$API_URL" > /dev/null; then
    echo "$(date): API is healthy" >> "$LOG_FILE"
else
    echo "$(date): API is unhealthy" >> "$LOG_FILE"
    # Restart service if unhealthy
    systemctl restart failsafe
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): Disk usage is high: ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEMORY_USAGE" -gt 80 ]; then
    echo "$(date): Memory usage is high: ${MEMORY_USAGE}%" >> "$LOG_FILE"
fi
EOF

    chmod +x /opt/failsafe/scripts/monitor.sh
    chown -R "$SERVICE_USER:$SERVICE_GROUP" /opt/failsafe/scripts

    # Add monitoring to crontab
    echo "*/5 * * * * root /opt/failsafe/scripts/monitor.sh" >> /etc/cron.d/failsafe-monitor
}

create_environment_file() {
    log_info "Creating environment file..."
    
    # Get database password
    DB_PASSWORD=$(sudo -u postgres psql -t -c "SELECT password FROM pg_shadow WHERE usename='failsafe_user';" | xargs)
    
    # Get Redis password
    REDIS_PASSWORD=$(cat /opt/failsafe/redis_password)
    
    # Create environment file
    cat > /opt/failsafe/.env << EOF
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=FailSafe
VERSION=1.0.0
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://failsafe_user:${DB_PASSWORD}@localhost:5432/failsafe
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/failsafe/app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
RATE_LIMIT_BURST=100

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Monitoring
ENABLE_MONITORING=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_ENDPOINT=/health
PROMETHEUS_ENDPOINT=/prometheus

# Backup
BACKUP_DIR=/var/backups/failsafe
BACKUP_RETENTION_DAYS=30
EOF

    chown "$SERVICE_USER:$SERVICE_GROUP" /opt/failsafe/.env
    chmod 600 /opt/failsafe/.env
}

setup_ssl() {
    log_info "Setting up SSL certificate..."
    
    # Check if domain is provided
    if [ -z "$1" ]; then
        log_warn "No domain provided. SSL setup skipped."
        log_warn "To setup SSL later, run: certbot --nginx -d yourdomain.com"
        return
    fi
    
    DOMAIN=$1
    
    # Obtain SSL certificate
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
    
    # Setup auto-renewal
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
}

main() {
    log_info "Starting FailSafe production setup..."
    
    # Check if running as root
    check_root
    
    # Install dependencies
    install_dependencies
    
    # Create user
    create_user
    
    # Setup directories
    setup_directories
    
    # Setup database
    setup_database
    
    # Setup Redis
    setup_redis
    
    # Setup Nginx
    setup_nginx
    
    # Setup firewall
    setup_firewall
    
    # Setup Fail2ban
    setup_fail2ban
    
    # Setup systemd service
    setup_systemd_service
    
    # Setup cron jobs
    setup_cron_jobs
    
    # Setup monitoring
    setup_monitoring
    
    # Create environment file
    create_environment_file
    
    # Setup SSL if domain provided
    if [ ! -z "$1" ]; then
        setup_ssl "$1"
    fi
    
    log_info "Production setup completed!"
    log_info "Next steps:"
    log_info "1. Deploy your application code to $PROJECT_DIR"
    log_info "2. Install Python dependencies: cd $PROJECT_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    log_info "3. Run database migrations: alembic upgrade head"
    log_info "4. Start the service: systemctl start failsafe"
    log_info "5. Check status: systemctl status failsafe"
    log_info "6. View logs: journalctl -u failsafe -f"
}

# Run main function
main "$@"






