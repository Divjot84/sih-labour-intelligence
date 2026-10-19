"""
FastAPI application entrypoint.

Run from the backend/ directory:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    dashboard,
    forecasts,
    health,
    ingestion,
    jobs,
    mgnrega,
    skills,
)
from app.core.config import settings

app = FastAPI(
    title="Labour Market Intelligence API",
    description="SIH26246 — AI-Enabled Labour Market Intelligence & Skill Demand Forecasting",
    version="0.1.0",
)

# CORS — allow only the frontend origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(skills.router)
app.include_router(mgnrega.router)
app.include_router(forecasts.router)
app.include_router(ingestion.router)


@app.get("/")
def root():
    return {"name": "Labour Market Intelligence API", "docs": "/docs", "health": "/health"}
