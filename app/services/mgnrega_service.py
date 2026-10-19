"""Service layer for MGNREGA queries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.mgnrega import MgnregaRecord


def get_records(
    db: Session,
    state: str | None = None,
    district: str | None = None,
    financial_year: str | None = None,
    month: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(MgnregaRecord)
    if state:
        q = q.filter(MgnregaRecord.state_name.ilike(f"%{state}%"))
    if district:
        q = q.filter(MgnregaRecord.district_name.ilike(f"%{district}%"))
    if financial_year:
        q = q.filter(MgnregaRecord.financial_year == financial_year)
    if month:
        q = q.filter(MgnregaRecord.month == month)

    total = q.count()
    records = q.offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [_serialize(r) for r in records],
    }


def get_indicators(
    db: Session,
    state: str | None = None,
    district: str | None = None,
    financial_year: str | None = None,
) -> list[dict]:
    q = db.query(MgnregaRecord)
    if state:
        q = q.filter(MgnregaRecord.state_name.ilike(f"%{state}%"))
    if district:
        q = q.filter(MgnregaRecord.district_name.ilike(f"%{district}%"))
    if financial_year:
        q = q.filter(MgnregaRecord.financial_year == financial_year)

    return [_serialize(r) for r in q.order_by(MgnregaRecord.financial_year, MgnregaRecord.month).all()]


def _serialize(r: MgnregaRecord) -> dict:
    return {
        "id": r.id,
        "financial_year": r.financial_year,
        "month": r.month,
        "state_name": r.state_name,
        "district_name": r.district_name,
        "households_worked": r.households_worked,
        "individuals_worked": r.individuals_worked,
        "active_workers": r.active_workers,
        "active_job_cards": r.active_job_cards,
        "average_days_employment_per_household": r.average_days_employment_per_household,
        "average_daily_wage": r.average_daily_wage,
        "women_persondays": r.women_persondays,
        "total_expenditure": r.total_expenditure,
    }
