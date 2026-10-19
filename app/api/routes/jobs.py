"""Job posting search endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.job_service import get_jobs

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs")
def jobs(
    state: str | None = Query(None, description="Filter by state"),
    city: str | None = Query(None, description="Filter by city"),
    search: str | None = Query(None, description="Search in job title"),
    min_experience: float | None = Query(None, ge=0),
    max_experience: float | None = Query(None, ge=0),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search and filter job postings with pagination."""
    return get_jobs(
        db,
        state=state,
        city=city,
        search=search,
        min_experience=min_experience,
        max_experience=max_experience,
        offset=offset,
        limit=limit,
    )
