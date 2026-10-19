"""Forecast results endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.forecast_service import get_forecasts

router = APIRouter(prefix="/api/v1", tags=["forecasts"])


@router.get("/forecasts")
def forecasts(
    skill: str | None = Query(None),
    region: str | None = Query(None),
    horizon: int | None = Query(None, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """
    Return stored ML forecasts, or an INSUFFICIENT_HISTORY error
    when no time-series data is available.
    """
    return get_forecasts(db, skill=skill, region=region, horizon=horizon)
