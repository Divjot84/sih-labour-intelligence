"""Service layer for the dashboard summary endpoint."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.data_source import DataSource, IngestionRun
from app.models.job_posting import JobPosting, JobSkill, Skill
from app.models.mgnrega import MgnregaRecord

LIMITATIONS = [
    "Job-posting records represent the supplied dataset only, not all Indian vacancies.",
    "MGNREGA data is a rural employment programme indicator, not a measure of all employment.",
    "Forecasting is unavailable until reliable historical time-series data is available.",
    "Relative date labels such as 'Today' or '6 Days Ago' cannot be converted to exact dates.",
]


def get_dashboard_summary(db: Session) -> dict:
    job_count: int = db.query(func.count(JobPosting.id)).scalar() or 0
    skill_count: int = db.query(func.count(Skill.id)).scalar() or 0

    # Top 5 skills by job count
    top_skills_query = (
        db.query(Skill.canonical_name, func.count(JobSkill.job_id).label("job_count"))
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .group_by(Skill.canonical_name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(5)
        .all()
    )
    top_skills = [{"skill": row[0], "job_count": row[1]} for row in top_skills_query]

    states_covered: int = (
        db.query(func.count(func.distinct(MgnregaRecord.state_name))).scalar() or 0
    )
    districts_covered: int = (
        db.query(func.count(func.distinct(MgnregaRecord.district_name))).scalar() or 0
    )

    # Latest MGNREGA period
    latest_period = (
        db.query(MgnregaRecord.financial_year, MgnregaRecord.month)
        .filter(MgnregaRecord.financial_year.isnot(None))
        .order_by(MgnregaRecord.financial_year.desc(), MgnregaRecord.month.desc())
        .first()
    )
    mgnrega_latest = (
        f"{latest_period[0]} {latest_period[1]}" if latest_period else None
    )

    return {
        "data_coverage": {
            "job_market_snapshot_date": None,  # relative dates only in dataset
            "mgnrega_latest_period": mgnrega_latest,
        },
        "job_market": {
            "records_in_dataset": job_count,
            "distinct_skills": skill_count,
            "top_skills": top_skills,
        },
        "mgnrega": {
            "states_covered": states_covered,
            "districts_covered": districts_covered,
        },
        "limitations": LIMITATIONS,
    }


def get_meta(db: Session) -> dict:
    sources = db.query(DataSource).filter(DataSource.active.is_(True)).all()
    return {
        "sources": [
            {
                "name": s.name,
                "source_type": s.source_type,
                "publisher": s.publisher,
                "licence": s.licence,
                "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
            }
            for s in sources
        ]
    }
