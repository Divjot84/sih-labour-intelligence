"""
Admin ingestion status endpoint.

Trigger endpoints (POST /admin/ingestion/mgnrega and /admin/ingestion/jobs)
are intentionally left as stubs. For a hackathon demo, run imports from
the terminal; add authentication before exposing them publicly.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import IngestionRun

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.get("/ingestion/status")
def ingestion_status(db: Session = Depends(get_db)):
    """Latest ingestion run per source."""
    runs = (
        db.query(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": r.id,
            "source_id": r.source_id,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "status": r.status,
            "records_inserted": r.records_inserted,
            "records_updated": r.records_updated,
            "records_rejected": r.records_rejected,
        }
        for r in runs
    ]
