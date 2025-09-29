from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from .api.v1.router import api_router
from .db.session import Base, engine
from .core.middleware import RequestIDLoggingMiddleware, RateLimitMiddleware
from .core.config import get_settings
from .services.monitoring_service import monitoring_service
from .services.embedding_service import get_embedding_model
import logging


def create_app() -> FastAPI:
    app = FastAPI(
        title="FailSafe API", 
        version="0.1.0",
        description="AI-Powered Fact-Checking and Misinformation Analysis System",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    settings = get_settings()
    
    # Add middleware in order (last added = first executed)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(RequestIDLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, max_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize monitoring service
    monitoring_service.start_monitoring()
    
    # Setup logging
    logging.basicConfig(level=getattr(logging, settings.logging_level))
    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Start monitoring
        monitoring_service.start_monitoring()
        # Preload embedding model to reduce first-request latency
        get_embedding_model()
        logging.info("FailSafe API started successfully")
    except Exception as e:
        logging.error(f"Failed to start FailSafe API: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        monitoring_service.stop_monitoring()
        logging.info("FailSafe API shutdown complete")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")


