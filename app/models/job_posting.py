"""ORM models for job postings, skills and the many-to-many link."""

import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Skill(Base):
    """Canonical skill entity (Python, SQL, Power BI …)."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )

    job_links: Mapped[list["JobSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class JobPosting(Base):
    """One job record from the Excel snapshot."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )
    source_job_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    title_normalized: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_raw: Mapped[str | None] = mapped_column(String(300), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    minimum_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    minimum_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Only store a real datetime when known; never convert a relative label
    posted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    relative_posted_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_record_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    skill_links: Mapped[list["JobSkill"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_job_state_city_title", "state", "city", "title_normalized"),
    )


class JobSkill(Base):
    """Many-to-many link between JobPosting and Skill."""

    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    extraction_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="tags"
    )  # tags / description / manual
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped[JobPosting] = relationship(back_populates="skill_links")
    skill: Mapped[Skill] = relationship(back_populates="job_links")

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", "extraction_method", name="uq_job_skill_method"),
        Index("ix_job_skills_skill_id", "skill_id", "job_id"),
    )
