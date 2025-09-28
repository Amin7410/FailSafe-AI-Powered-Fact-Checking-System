"""
Security utilities and middleware for FailSafe
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Main security manager for FailSafe"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security_scheme = HTTPBearer()
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = hashed_password.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hmac.compare_digest(pwd_hash.hex(), hash_hex)
        except ValueError:
            return False
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format"""
        return len(api_key) >= 32 and api_key.isalnum()
    
    def create_hmac_signature(self, data: str, secret: str) -> str:
        """Create HMAC signature for data integrity"""
        return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def verify_hmac_signature(self, data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected_signature = self.create_hmac_signature(data, secret)
        return hmac.compare_digest(signature, expected_signature)

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        window_start = now - self.window_seconds
        
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > window_start
            ]
            return max(0, self.max_requests - len(self.requests[client_id]))
        
        return self.max_requests

class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_language(language: str) -> bool:
        """Validate language code"""
        valid_languages = ['en', 'es', 'fr', 'de', 'zh', 'ar', 'ja', 'ko', 'ru']
        return language in valid_languages
    
    @staticmethod
    def validate_confidence_threshold(threshold: float) -> bool:
        """Validate confidence threshold"""
        return 0.0 <= threshold <= 1.0

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(request: Request, response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("security.audit")
    
    def log_authentication_attempt(self, client_ip: str, user_id: str, success: bool):
        """Log authentication attempt"""
        self.logger.info(
            f"Authentication attempt: client_ip={client_ip}, user_id={user_id}, success={success}",
            extra={
                "event_type": "authentication",
                "client_ip": client_ip,
                "user_id": user_id,
                "success": success
            }
        )
    
    def log_api_access(self, client_ip: str, endpoint: str, method: str, user_id: str = None):
        """Log API access"""
        self.logger.info(
            f"API access: client_ip={client_ip}, endpoint={endpoint}, method={method}, user_id={user_id}",
            extra={
                "event_type": "api_access",
                "client_ip": client_ip,
                "endpoint": endpoint,
                "method": method,
                "user_id": user_id
            }
        )
    
    def log_security_event(self, event_type: str, client_ip: str, details: Dict[str, Any]):
        """Log security event"""
        self.logger.warning(
            f"Security event: {event_type}, client_ip={client_ip}, details={details}",
            extra={
                "event_type": "security_event",
                "security_event_type": event_type,
                "client_ip": client_ip,
                "details": details
            }
        )
    
    def log_rate_limit_exceeded(self, client_ip: str, endpoint: str):
        """Log rate limit exceeded"""
        self.logger.warning(
            f"Rate limit exceeded: client_ip={client_ip}, endpoint={endpoint}",
            extra={
                "event_type": "rate_limit_exceeded",
                "client_ip": client_ip,
                "endpoint": endpoint
            }
        )

class DataEncryption:
    """Data encryption utilities"""
    
    def __init__(self, key: str):
        self.key = key.encode('utf-8')
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        from cryptography.fernet import Fernet
        f = Fernet(self.key)
        encrypted_data = f.encrypt(data.encode('utf-8'))
        return encrypted_data.hex()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        from cryptography.fernet import Fernet
        f = Fernet(self.key)
        decrypted_data = f.decrypt(bytes.fromhex(encrypted_data))
        return decrypted_data.decode('utf-8')
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self, rate_limiter: RateLimiter, audit_logger: AuditLogger):
        self.rate_limiter = rate_limiter
        self.audit_logger = audit_logger
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware"""
        client_ip = request.client.host
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            self.audit_logger.log_rate_limit_exceeded(client_ip, str(request.url))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Log API access
        self.audit_logger.log_api_access(
            client_ip, 
            str(request.url), 
            request.method
        )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        SecurityHeaders.add_security_headers(request, response)
        
        return response






