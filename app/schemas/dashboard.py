"""Pydantic response schemas for the dashboard and meta endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class DataCoverageOut(BaseModel):
    job_market_snapshot_date: str | None = None
    mgnrega_latest_period: str | None = None


class JobMarketSummaryOut(BaseModel):
    records_in_dataset: int
    distinct_skills: int
    top_skills: list[dict]


class MgnregaSummaryOut(BaseModel):
    states_covered: int
    districts_covered: int


class DashboardSummaryOut(BaseModel):
    data_coverage: DataCoverageOut
    job_market: JobMarketSummaryOut
    mgnrega: MgnregaSummaryOut
    limitations: list[str]


class MetaOut(BaseModel):
    sources: list[dict]
