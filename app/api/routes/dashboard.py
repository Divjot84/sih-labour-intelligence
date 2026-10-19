"""Dashboard summary and metadata endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import get_dashboard_summary, get_meta

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    """Data source names, publishers and last update timestamps."""
    return get_meta(db)


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """KPI cards: job count, top skills, MGNREGA coverage, limitations."""
    return get_dashboard_summary(db)
