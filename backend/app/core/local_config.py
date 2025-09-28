"""
Local Development Configuration

Provides configuration for local development without Docker.
Uses SQLite instead of PostgreSQL and local file storage.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from .config import Settings


class LocalSettings(Settings):
    """Local development settings with SQLite and file storage"""
    
    def __init__(self):
        super().__init__()
        self._setup_local_paths()
    
    def _setup_local_paths(self):
        """Setup local file paths for development"""
        self.base_dir = Path(__file__).resolve().parents[3]
        self.data_dir = self.base_dir / "data"
        self.cache_dir = self.data_dir / "cache"
        self.models_dir = self.data_dir / "models"
        self.logs_dir = self.base_dir / "logs"
        
        # Create directories if they don't exist
        for dir_path in [self.data_dir, self.cache_dir, self.models_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """SQLite database URL for local development"""
        db_path = self.data_dir / "failsafe.db"
        return f"sqlite:///{db_path}"
    
    @property
    def redis_url(self) -> str:
        """Redis URL - use SQLite fallback if Redis not available"""
        return os.getenv("REDIS_URL", "sqlite:///cache.db")
    
    @property
    def neo4j_uri(self) -> str:
        """Neo4j URI for local development"""
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    @property
    def neo4j_user(self) -> str:
        """Neo4j username"""
        return os.getenv("NEO4J_USER", "neo4j")
    
    @property
    def neo4j_password(self) -> str:
        """Neo4j password"""
        return os.getenv("NEO4J_PASSWORD", "password")
    
    @property
    def cache_config(self) -> Dict[str, Any]:
        """Local cache configuration"""
        return {
            "type": "file" if "sqlite" in self.redis_url else "redis",
            "path": str(self.cache_dir) if "sqlite" in self.redis_url else None,
            "url": self.redis_url,
            "ttl": self.cache["memory_ttl_seconds"],
            "max_size": self.cache["max_memory_items"]
        }
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """Local model configuration"""
        return {
            "models_dir": str(self.models_dir),
            "cache_dir": str(self.cache_dir),
            "download_models": True,
            "use_local_models": True,
            "quantization": self.performance["model_quantization"],
            "device": "cpu"  # Use CPU for local development
        }
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Local logging configuration"""
        return {
            "level": self.logging_level,
            "format": self.log_format,
            "file": str(self.logs_dir / "failsafe.log"),
            "max_size": "10MB",
            "backup_count": 5,
            "structured": self.structured_logging
        }
    
    @property
    def development_config(self) -> Dict[str, Any]:
        """Development-specific configuration"""
        return {
            "debug": True,
            "reload": True,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 1,
            "log_level": "debug",
            "access_log": True,
            "use_colors": True
        }
    
    @property
    def external_apis(self) -> Dict[str, Any]:
        """External API configuration"""
        return {
            "pubmed_api_key": os.getenv("PUBMED_API_KEY", ""),
            "huggingface_token": os.getenv("HUGGINGFACE_TOKEN", ""),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Security configuration for local development"""
        return {
            "secret_key": os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            "jwt_secret": os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production"),
            "jwt_algorithm": "HS256",
            "jwt_expiration": 3600,  # 1 hour
            "cors_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "rate_limiting": self.security["rate_limiting"],
            "max_requests_per_minute": self.rate_limit_per_minute
        }
    
    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Monitoring configuration for local development"""
        return {
            "enabled": True,
            "metrics_endpoint": "/metrics",
            "health_endpoint": "/health",
            "prometheus_enabled": False,  # Disable for local dev
            "log_requests": True,
            "log_responses": False,  # Disable for performance
            "performance_tracking": True
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "echo": False,  # Set to True for SQL debugging
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        if "sqlite" in self.redis_url:
            return {
                "type": "sqlite",
                "path": str(self.cache_dir / "cache.db"),
                "timeout": 5
            }
        else:
            return {
                "type": "redis",
                "url": self.redis_url,
                "timeout": 5,
                "retry_on_timeout": True,
                "decode_responses": True
            }
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration"""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password,
            "max_connection_lifetime": 3600,
            "max_connection_pool_size": 50,
            "connection_timeout": 30
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            "app": {
                "name": self.app_name,
                "version": self.version,
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "database": self.get_database_config(),
            "redis": self.get_redis_config(),
            "neo4j": self.get_neo4j_config(),
            "cache": self.cache_config,
            "model": self.model_config,
            "logging": self.logging_config,
            "development": self.development_config,
            "external_apis": self.external_apis,
            "security": self.security_config,
            "monitoring": self.monitoring_config,
            "ethical": self.ethical
        }


# Global instance for local development
def get_local_settings() -> LocalSettings:
    """Get local development settings"""
    return LocalSettings()

