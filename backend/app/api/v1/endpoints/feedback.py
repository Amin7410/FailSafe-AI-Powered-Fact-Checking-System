from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import Feedback as FeedbackORM


class FeedbackRequest(BaseModel):
    claim_id: str = Field(..., description="Identifier of the analyzed claim")
    helpful: bool = Field(..., description="Whether the report was helpful")
    comments: str | None = Field(None, description="Optional user comments")


class FeedbackResponse(BaseModel):
    status: str


router = APIRouter(prefix="/feedback")


@router.post("", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    fb = FeedbackORM(claim_id=payload.claim_id, helpful=payload.helpful, comments=payload.comments)
    db.add(fb)
    db.commit()
    return FeedbackResponse(status="received")


class FeedbackItem(BaseModel):
    id: int
    claim_id: str
    helpful: bool
    comments: str | None = None
    created_at: str


class FeedbackListResponse(BaseModel):
    total: int
    items: list[FeedbackItem]


@router.get("", response_model=FeedbackListResponse)
def list_feedback(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> FeedbackListResponse:
    total = db.query(func.count(FeedbackORM.id)).scalar() or 0
    rows = (
        db.query(FeedbackORM)
        .order_by(FeedbackORM.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    items = [
        FeedbackItem(
            id=row.id,
            claim_id=row.claim_id,
            helpful=row.helpful,
            comments=row.comments,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
    return FeedbackListResponse(total=total, items=items)


