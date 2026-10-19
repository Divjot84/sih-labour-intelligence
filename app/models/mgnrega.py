"""ORM model for MGNREGA district-wise records."""

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
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MgnregaRecord(Base):
    """One MGNREGA district/period row from Data.gov.in."""

    __tablename__ = "mgnrega_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )
    financial_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    month: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    households_worked: Mapped[float | None] = mapped_column(Float, nullable=True)
    individuals_worked: Mapped[float | None] = mapped_column(Float, nullable=True)
    active_workers: Mapped[float | None] = mapped_column(Float, nullable=True)
    active_job_cards: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_days_employment_per_household: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    average_daily_wage: Mapped[float | None] = mapped_column(Float, nullable=True)
    women_persondays: Mapped[float | None] = mapped_column(Float, nullable=True)
    sc_persondays: Mapped[float | None] = mapped_column(Float, nullable=True)
    st_persondays: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_expenditure: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_record_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retrieved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "financial_year",
            "month",
            "state_code",
            "district_code",
            name="uq_mgnrega_period_geography",
        ),
        Index("ix_mgnrega_state_district_period", "state_name", "district_name", "financial_year", "month"),
    )
