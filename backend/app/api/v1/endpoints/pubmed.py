from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.pubmed_service import PubMedService


router = APIRouter(prefix="/pubmed")


class SeedResponse(BaseModel):
    added: int


@router.post("/seed", response_model=SeedResponse)
def seed_pubmed(q: str = Query(..., description="search query"), retmax: int = Query(10, ge=1, le=50)) -> SeedResponse:
    try:
        svc = PubMedService()
        added = svc.seed_cache(query=q, retmax=retmax)
        return SeedResponse(added=added)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))



