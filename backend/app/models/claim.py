from pydantic import BaseModel, Field, HttpUrl
from typing import Any, Dict, Optional


class ClaimRequest(BaseModel):
    text: str | None = Field(None, description="Raw text of the claim to analyze")
    url: HttpUrl | None = Field(None, description="Optional URL to fetch and analyze")
    language: str = Field("en", description="ISO language code of the input")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for AI detection")



