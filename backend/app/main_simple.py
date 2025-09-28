"""
Simple FastAPI app for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FailSafe API", 
    version="0.1.0",
    description="AI-Powered Fact-Checking and Misinformation Analysis System"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FailSafe API is running!"}

@app.get("/health/liveness")
def liveness():
    return {"status": "ok"}

@app.get("/health/readiness")
def readiness():
    return {"status": "ready"}

@app.post("/api/v1/analyze")
def analyze_claim(payload: dict):
    """Simple analyze endpoint for testing"""
    return {
        "claim_id": "test-123",
        "verdict": "Mixed",
        "confidence": 0.75,
        "evidence": [
            {
                "source": "Example Source",
                "title": "Test Evidence",
                "relevance_score": 0.8,
                "credibility_score": 0.7
            }
        ],
        "verification": {
            "is_verified": True,
            "confidence": 0.75,
            "reasoning": "Test verification",
            "sources_checked": 1,
            "contradictory_sources": 0,
            "supporting_sources": 1
        },
        "fallacies": [],
        "sag": {
            "nodes": [],
            "edges": []
        },
        "multilingual_data": None,
        "ai_detection": {
            "is_ai_generated": False,
            "confidence": 0.3,
            "method": "test",
            "scores": {},
            "details": {}
        },
        "processing_time_ms": 1000,
        "meta_data": {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






