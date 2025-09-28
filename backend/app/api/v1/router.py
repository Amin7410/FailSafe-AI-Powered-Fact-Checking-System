from fastapi import APIRouter
from .endpoints import (
    analyze, feedback, health, pubmed, monitor, docs, 
    provenance, collaboration, monitoring, testing, backup
)

api_router = APIRouter()
api_router.include_router(analyze.router, tags=["analyze"])
api_router.include_router(feedback.router, tags=["feedback"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(pubmed.router, tags=["pubmed"])
api_router.include_router(monitor.router, tags=["monitor"])
api_router.include_router(monitoring.router, tags=["monitoring"])
api_router.include_router(testing.router, tags=["testing"])
api_router.include_router(backup.router, tags=["backup"])
api_router.include_router(docs.router, tags=["docs"])
api_router.include_router(provenance.router, tags=["provenance"])
api_router.include_router(collaboration.router, tags=["collaboration"])


