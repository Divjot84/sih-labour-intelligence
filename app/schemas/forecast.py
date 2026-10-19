"""Pydantic response schemas for forecast endpoints."""

from __future__ import annotations

import datetime

from pydantic import BaseModel


class ForecastOut(BaseModel):
    id: int
    metric_name: str
    region_code: str | None = None
    target_period: str
    predicted_value: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    unit: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    generated_at: datetime.datetime
    training_cutoff: datetime.datetime | None = None
    status: str
    notes: str | None = None

    model_config = {"from_attributes": True}


class ForecastUnavailableOut(BaseModel):
    detail: dict  # {"code": "INSUFFICIENT_HISTORY", "message": "..."}
