"""MGNREGA data endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.mgnrega_service import get_indicators, get_records

router = APIRouter(prefix="/api/v1", tags=["mgnrega"])


@router.get("/mgnrega/records")
def mgnrega_records(
    state: str | None = Query(None),
    district: str | None = Query(None),
    financial_year: str | None = Query(None, example="2024-2025"),
    month: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Paginated MGNREGA district rows with optional filters."""
    return get_records(db, state=state, district=district,
                       financial_year=financial_year, month=month,
                       offset=offset, limit=limit)


@router.get("/mgnrega/indicators")
def mgnrega_indicators(
    state: str | None = Query(None),
    district: str | None = Query(None),
    financial_year: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Aggregated indicator time series for charts."""
    return get_indicators(db, state=state, district=district,
                          financial_year=financial_year)
