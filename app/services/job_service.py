"""Service layer for job and skill queries."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.job_posting import JobPosting, JobSkill, Skill


def get_jobs(
    db: Session,
    state: str | None = None,
    city: str | None = None,
    search: str | None = None,
    min_experience: float | None = None,
    max_experience: float | None = None,
    offset: int = 0,
    limit: int = 20,
) -> dict:
    q = db.query(JobPosting)
    if state:
        q = q.filter(JobPosting.state.ilike(f"%{state}%"))
    if city:
        q = q.filter(JobPosting.city.ilike(f"%{city}%"))
    if search:
        q = q.filter(JobPosting.title_normalized.ilike(f"%{search.lower()}%"))
    if min_experience is not None:
        q = q.filter(JobPosting.minimum_experience >= min_experience)
    if max_experience is not None:
        q = q.filter(JobPosting.maximum_experience <= max_experience)

    total = q.count()
    jobs = q.offset(offset).limit(limit).all()

    items = []
    for job in jobs:
        skill_names = [
            link.skill.canonical_name
            for link in db.query(JobSkill)
            .filter(JobSkill.job_id == job.id)
            .join(Skill)
            .all()
        ]
        items.append(
            {
                "id": job.id,
                "title": job.title,
                "title_normalized": job.title_normalized,
                "location_raw": job.location_raw,
                "state": job.state,
                "city": job.city,
                "minimum_salary": job.minimum_salary,
                "maximum_salary": job.maximum_salary,
                "minimum_experience": job.minimum_experience,
                "maximum_experience": job.maximum_experience,
                "relative_posted_label": job.relative_posted_label,
                "skills": skill_names,
            }
        )

    return {"total": total, "offset": offset, "limit": limit, "items": items}


def get_top_skills(
    db: Session,
    state: str | None = None,
    limit: int = 15,
) -> list[dict]:
    q = (
        db.query(Skill.canonical_name, func.count(JobSkill.job_id).label("job_count"))
        .join(JobSkill, Skill.id == JobSkill.skill_id)
    )
    if state:
        q = q.join(JobPosting, JobSkill.job_id == JobPosting.id).filter(
            JobPosting.state.ilike(f"%{state}%")
        )
    results = (
        q.group_by(Skill.canonical_name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(limit)
        .all()
    )
    return [{"skill": row[0], "job_count": row[1]} for row in results]


def get_skills_by_region(db: Session, limit: int = 20) -> list[dict]:
    """Return top skills per state."""
    results = (
        db.query(
            JobPosting.state,
            Skill.canonical_name,
            func.count(JobSkill.job_id).label("job_count"),
        )
        .join(JobSkill, JobPosting.id == JobSkill.job_id)
        .join(Skill, JobSkill.skill_id == Skill.id)
        .filter(JobPosting.state.isnot(None))
        .group_by(JobPosting.state, Skill.canonical_name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(limit)
        .all()
    )
    return [{"state": r[0], "skill": r[1], "job_count": r[2]} for r in results]
