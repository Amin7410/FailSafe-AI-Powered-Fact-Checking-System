from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/health")


@router.get("/live")
def liveness():
    return {"status": "ok"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    # Simple DB check
    db.execute("SELECT 1")
    return {"status": "ready"}


