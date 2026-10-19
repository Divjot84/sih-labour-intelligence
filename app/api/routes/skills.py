"""Skills endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.job_service import get_skills_by_region, get_top_skills

router = APIRouter(prefix="/api/v1", tags=["skills"])


@router.get("/skills/top")
def top_skills(
    state: str | None = Query(None),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Top skills ranked by number of job records that mention them."""
    return get_top_skills(db, state=state, limit=limit)


@router.get("/skills/by-region")
def skills_by_region(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Top skills broken down by state."""
    return get_skills_by_region(db, limit=limit)
