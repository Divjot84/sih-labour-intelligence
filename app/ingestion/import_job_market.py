"""
Import the Indian Job Market Excel snapshot into PostgreSQL.

Run from the backend/ directory:
    python -m app.ingestion.import_job_market
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.data_source import DataSource, IngestionRun
from app.models.job_posting import JobPosting, JobSkill, Skill

# ---------------------------------------------------------------------------
# Skill alias map: normalize common variants to a canonical name.
# Extend this map as you find variants in the data.
# ---------------------------------------------------------------------------
SKILL_ALIAS: dict[str, str] = {
    "python3": "Python",
    "py": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "reactjs": "React",
    "react.js": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "sql server": "SQL Server",
    "ms sql": "SQL Server",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "natural language processing": "NLP",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "ms excel": "Excel",
    "microsoft excel": "Excel",
}


def _canonical_skill(raw: str) -> str:
    stripped = raw.strip()
    lower = stripped.lower()
    return SKILL_ALIAS.get(lower, stripped.title())


def _split_skills(tags_cell: str) -> list[str]:
    """Split a tagsAndSkills cell into individual skill strings."""
    if not isinstance(tags_cell, str) or not tags_cell.strip():
        return []
    # Try comma, then pipe, then semicolon
    for sep in (",", "|", ";"):
        if sep in tags_cell:
            parts = tags_cell.split(sep)
            return [p.strip() for p in parts if p.strip()]
    return [tags_cell.strip()]


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _row_hash(row: pd.Series) -> str:
    row_str = json.dumps(row.astype(str).to_dict(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(row_str.encode()).hexdigest()


def _normalize_location(raw: str | None) -> tuple[str | None, str | None]:
    """Very simple heuristic: last comma-segment is treated as state, rest as city."""
    if not raw or not isinstance(raw, str):
        return None, None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return parts[0], None


def _get_or_create_skill(db: Session, name: str) -> Skill:
    skill = db.query(Skill).filter(Skill.canonical_name == name).first()
    if skill is None:
        skill = Skill(canonical_name=name)
        db.add(skill)
        db.flush()
    return skill


def run_import(xlsx_path: str | None = None) -> None:
    path = xlsx_path or settings.JOB_MARKET_XLSX_PATH
    if not os.path.exists(path):
        print(f"[ERROR] Excel file not found: {path}", file=sys.stderr)
        sys.exit(1)

    db: Session = SessionLocal()
    try:
        # ---- register / retrieve data source ---------------------------------
        source = db.query(DataSource).filter(DataSource.name == "Indian Job Market 2025").first()
        if source is None:
            source = DataSource(
                name="Indian Job Market 2025",
                source_type="xlsx",
                source_url=None,
                publisher="Unknown â€“ verify licence before public deployment",
                licence="unknown_pending_verification",
            )
            db.add(source)
            db.flush()

        run = IngestionRun(source_id=source.id, started_at=datetime.datetime.utcnow())
        db.add(run)
        db.flush()

        # ---- load Excel ------------------------------------------------------
        print(f"Loading {path} â€¦")
        df = pd.read_excel(path, engine="openpyxl")
        print(f"Columns found: {list(df.columns)}")
        print(f"Rows read    : {len(df)}")

        # Normalise column names (strip spaces, lowercase for lookup)
        col_map = {c: c.strip() for c in df.columns}
        df.rename(columns=col_map, inplace=True)
        lower_cols = {c.lower(): c for c in df.columns}

        def col(name: str) -> str | None:
            """Return actual column name for a case-insensitive lookup."""
            return lower_cols.get(name.lower())

        title_col = col("title")
        tags_col = col("tagsAndSkills") or col("tags_and_skills") or col("tagsandskills")
        location_col = col("location")
        min_sal_col = col("minimumSalary") or col("minimumsalary")
        max_sal_col = col("maximumSalary") or col("maximumsalary")
        min_exp_col = col("minimumExperience") or col("minimumexperience")
        max_exp_col = col("maximumExperience") or col("maximumexperience")
        job_uploaded_col = col("jobUploaded") or col("jobuploaded")
        desc_col = col("jobDescription") or col("jobdescription")

        # ---- quality report --------------------------------------------------
        total_rows = len(df)
        exact_dupes = df.duplicated().sum()
        missing_title = df[title_col].isna().sum() if title_col else total_rows
        missing_location = df[location_col].isna().sum() if location_col else total_rows
        missing_skills = df[tags_col].isna().sum() if tags_col else total_rows

        print(f"\n--- Quality Report ---")
        print(f"Total rows         : {total_rows}")
        print(f"Exact duplicates   : {exact_dupes}")
        print(f"Missing title      : {missing_title}")
        print(f"Missing location   : {missing_location}")
        print(f"Missing skills     : {missing_skills}")
        print(f"---------------------\n")

        # Drop exact duplicates
        df.drop_duplicates(inplace=True)

        seen_hashes: set[str] = set()
        inserted = updated = rejected = 0
        now = datetime.datetime.utcnow()

        for _, row in df.iterrows():
            row_hash = _row_hash(row)

            title_val = str(row[title_col]).strip() if title_col and pd.notna(row.get(title_col)) else None
            if not title_val:
                rejected += 1
                continue

            loc_raw = str(row[location_col]).strip() if location_col and pd.notna(row.get(location_col)) else None
            city, state = _normalize_location(loc_raw)

            raw_json = json.dumps(row.astype(str).to_dict(), ensure_ascii=False)

            # Check if record already exists by content hash
            existing = (
                db.query(JobPosting).filter(JobPosting.content_hash == row_hash).first()
            )
            if existing:
                existing.last_seen_at = now
                updated += 1
                continue

            if row_hash in seen_hashes:
                rejected += 1
                continue
            seen_hashes.add(row_hash)

            job = JobPosting(
                source_id=source.id,
                title=title_val,
                title_normalized=title_val.lower().strip(),
                location_raw=loc_raw,
                city=city,
                state=state,
                minimum_salary=_safe_float(row.get(min_sal_col)) if min_sal_col else None,
                maximum_salary=_safe_float(row.get(max_sal_col)) if max_sal_col else None,
                minimum_experience=_safe_float(row.get(min_exp_col)) if min_exp_col else None,
                maximum_experience=_safe_float(row.get(max_exp_col)) if max_exp_col else None,
                relative_posted_label=(
                    str(row[job_uploaded_col]).strip()
                    if job_uploaded_col and pd.notna(row.get(job_uploaded_col))
                    else None
                ),
                description=(
                    str(row[desc_col]).strip()
                    if desc_col and pd.notna(row.get(desc_col))
                    else None
                ),
                first_seen_at=now,
                last_seen_at=now,
                content_hash=row_hash,
                raw_record_json=raw_json,
            )
            db.add(job)
            db.flush()

            # Skill extraction
            seen_skill_ids = set()
            raw_tags = row.get(tags_col, "") if tags_col else ""
            for raw_skill in _split_skills(raw_tags):
                # Reject malformed tags that are actually full descriptions.
                if len(raw_skill) > 100 or len(raw_skill.split()) > 12:
                    continue
                canonical = _canonical_skill(raw_skill)
                if not canonical:
                    continue
                skill_obj = _get_or_create_skill(db, canonical)
                if skill_obj.id in seen_skill_ids:
                    continue
                seen_skill_ids.add(skill_obj.id)
                link = JobSkill(
                    job_id=job.id,
                    skill_id=skill_obj.id,
                    extraction_method="tags",
                    original_text=raw_skill,
                )
                db.add(link)

            inserted += 1

            if inserted % 5000 == 0:
                db.commit()
                print(f"  â€¦ committed {inserted} records so far")

        # ---- finalize run ----------------------------------------------------
        run.finished_at = datetime.datetime.utcnow()
        run.status = "success"
        run.records_seen = total_rows
        run.records_inserted = inserted
        run.records_updated = updated
        run.records_rejected = rejected
        source.retrieved_at = now

        db.commit()
        print(f"\nImport complete: inserted={inserted}, updated={updated}, rejected={rejected}")

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
