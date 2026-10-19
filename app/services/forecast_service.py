"""Service layer for forecast queries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.forecast import ForecastResult
from app.models.job_posting import Skill

INSUFFICIENT_HISTORY = {
    "code": "INSUFFICIENT_HISTORY",
    "message": (
        "A reliable historical time series is not available for this forecast. "
        "The current dataset is a single snapshot with only relative date labels. "
        "Forecasting will be enabled once multiple time-period snapshots with "
        "real timestamps are collected."
    ),
}


def get_forecasts(
    db: Session,
    skill: str | None = None,
    region: str | None = None,
    horizon: int | None = None,
) -> dict:
    q = db.query(ForecastResult)
    if skill:
        skill_obj = (
            db.query(Skill)
            .filter(Skill.canonical_name.ilike(f"%{skill}%"))
            .first()
        )
        if skill_obj is None:
            return {"detail": INSUFFICIENT_HISTORY}
        q = q.filter(ForecastResult.skill_id == skill_obj.id)
    if region:
        q = q.filter(ForecastResult.region_code.ilike(f"%{region}%"))

    results = q.order_by(ForecastResult.target_period).all()

    if not results:
        return {"detail": INSUFFICIENT_HISTORY}

    return {
        "forecasts": [
            {
                "id": r.id,
                "metric_name": r.metric_name,
                "region_code": r.region_code,
                "target_period": r.target_period,
                "predicted_value": r.predicted_value,
                "lower_bound": r.lower_bound,
                "upper_bound": r.upper_bound,
                "unit": r.unit,
                "model_name": r.model_name,
                "model_version": r.model_version,
                "generated_at": r.generated_at.isoformat(),
                "status": r.status,
            }
            for r in results
        ]
    }
