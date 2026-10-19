"""
Fetch MGNREGA district-wise data from the Data.gov.in API and store in PostgreSQL.

Run from the backend/ directory:
    python -m app.ingestion.import_mgnrega
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import time

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.data_source import DataSource, IngestionRun
from app.models.mgnrega import MgnregaRecord

API_BASE = "https://api.data.gov.in/resource"
PAGE_LIMIT = 1000
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Mapping from API field names to our normalized model fields
FIELD_MAP = {
    "financial_year": ["fin_year", "financial_year"],
    "month": ["month"],
    "state_code": ["state_code"],
    "state_name": ["state_name"],
    "district_code": ["district_code"],
    "district_name": ["district_name"],
    "households_worked": ["Total Households Worked", "total_households_worked"],
    "individuals_worked": ["Total Individuals Worked", "total_individuals_worked"],
    "active_workers": ["Total No Of Active Workers", "total_no_of_active_workers"],
    "active_job_cards": ["Total No Of Active Job Cards", "total_no_of_active_job_cards"],
    "average_days_employment_per_household": [
        "Average Days Of Employment Provided Per Household",
        "average_days_of_employment_provided_per_household",
    ],
    "average_daily_wage": [
        "Average Wage Rate Per Day Per Person",
        "average_wage_rate_per_day_per_person",
    ],
    "women_persondays": ["Women Persondays", "women_persondays"],
    "sc_persondays": ["SC Persondays", "sc_persondays"],
    "st_persondays": ["ST Persondays", "st_persondays"],
    "total_expenditure": ["Total Exp", "Total Expenditure", "total_exp", "total_expenditure"],
}


def _safe_float(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _get_field(record: dict, aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in record and record[alias] not in (None, ""):
            return record[alias]
    return None


def _record_hash(record: dict) -> str:
    key_parts = [
        str(record.get("financial_year", "")),
        str(record.get("month", "")),
        str(record.get("state_code", "")),
        str(record.get("district_code", "")),
    ]
    return hashlib.sha256("|".join(key_parts).encode()).hexdigest()


def fetch_page(offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
    """Fetch one page from the MGNREGA API with bounded retries."""
    if not settings.DATA_GOV_API_KEY:
        print("[ERROR] DATA_GOV_API_KEY is not set. Add it to .env", file=sys.stderr)
        sys.exit(1)

    url = f"{API_BASE}/{settings.DATA_GOV_MGNREGA_RESOURCE_ID}"
    params = {
        "api-key": settings.DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, httpx.ConnectError) as exc:
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries at offset {offset}")


def run_import() -> None:
    db: Session = SessionLocal()
    try:
        # ---- register / retrieve data source ---------------------------------
        source = db.query(DataSource).filter(DataSource.name == "MGNREGA District-wise").first()
        if source is None:
            source = DataSource(
                name="MGNREGA District-wise",
                source_type="api",
                source_url=f"{API_BASE}/{settings.DATA_GOV_MGNREGA_RESOURCE_ID}",
                publisher="Data.gov.in / Ministry of Rural Development",
                licence="Government Open Data",
            )
            db.add(source)
            db.flush()

        run = IngestionRun(source_id=source.id, started_at=datetime.datetime.utcnow())
        db.add(run)
        db.flush()

        # ---- paginate through API -------------------------------------------
        offset = 0
        total_seen = inserted = updated = rejected = 0
        now = datetime.datetime.utcnow()

        while True:
            print(f"Fetching offset={offset} …")
            data = fetch_page(offset=offset, limit=PAGE_LIMIT)
            records = data.get("records", [])
            if not records:
                break

            total_seen += len(records)

            for rec in records:
                normalized = {}
                for model_field, aliases in FIELD_MAP.items():
                    val = _get_field(rec, aliases)
                    if model_field not in ("financial_year", "month", "state_code",
                                           "state_name", "district_code", "district_name"):
                        normalized[model_field] = _safe_float(val)
                    else:
                        normalized[model_field] = val

                rec_hash = _record_hash(normalized)
                raw_json = json.dumps(rec, ensure_ascii=False)

                existing = (
                    db.query(MgnregaRecord)
                    .filter(MgnregaRecord.record_hash == rec_hash)
                    .first()
                )
                if existing:
                    updated += 1
                    continue

                record = MgnregaRecord(
                    source_id=source.id,
                    financial_year=normalized.get("financial_year"),
                    month=normalized.get("month"),
                    state_code=normalized.get("state_code"),
                    state_name=normalized.get("state_name"),
                    district_code=normalized.get("district_code"),
                    district_name=normalized.get("district_name"),
                    households_worked=normalized.get("households_worked"),
                    individuals_worked=normalized.get("individuals_worked"),
                    active_workers=normalized.get("active_workers"),
                    active_job_cards=normalized.get("active_job_cards"),
                    average_days_employment_per_household=normalized.get(
                        "average_days_employment_per_household"
                    ),
                    average_daily_wage=normalized.get("average_daily_wage"),
                    women_persondays=normalized.get("women_persondays"),
                    sc_persondays=normalized.get("sc_persondays"),
                    st_persondays=normalized.get("st_persondays"),
                    total_expenditure=normalized.get("total_expenditure"),
                    raw_record_json=raw_json,
                    record_hash=rec_hash,
                    retrieved_at=now,
                )
                db.add(record)
                inserted += 1

            db.commit()
            print(f"  Page done: {len(records)} records (total seen: {total_seen})")

            if len(records) < PAGE_LIMIT:
                break
            offset += PAGE_LIMIT

        # ---- finalize run ----------------------------------------------------
        run.finished_at = datetime.datetime.utcnow()
        run.status = "success"
        run.records_seen = total_seen
        run.records_inserted = inserted
        run.records_updated = updated
        run.records_rejected = rejected
        source.retrieved_at = now

        db.commit()
        print(
            f"\nMGNREGA import complete: "
            f"seen={total_seen}, inserted={inserted}, updated={updated}, rejected={rejected}"
        )

    except Exception as exc:
        db.rollback()
        if "run" in dir():
            run.status = "failed"
            run.error_summary = str(exc)[:500]
            run.finished_at = datetime.datetime.utcnow()
            db.commit()
        print(f"[ERROR] Import failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
