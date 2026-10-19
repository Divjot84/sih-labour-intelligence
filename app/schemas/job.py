"""Pydantic response schemas for job and skill endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class SkillOut(BaseModel):
    id: int
    canonical_name: str
    category: str | None = None

    model_config = {"from_attributes": True}


class SkillCountOut(BaseModel):
    """Skill name plus how many job records mention it."""

    skill: str
    job_count: int


class JobOut(BaseModel):
    id: int
    title: str | None = None
    title_normalized: str | None = None
    location_raw: str | None = None
    state: str | None = None
    city: str | None = None
    minimum_salary: float | None = None
    maximum_salary: float | None = None
    minimum_experience: float | None = None
    maximum_experience: float | None = None
    relative_posted_label: str | None = None
    skills: list[str] = []

    model_config = {"from_attributes": True}


class PaginatedJobs(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[JobOut]
