# SIH26246 — Labour Market Intelligence Backend

FastAPI backend for the AI-Enabled Labour Market Intelligence and Skill Demand–Supply Forecasting Engine.

## Quick Start

### 1. Create virtual environment & install dependencies

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```powershell
copy .env.example .env
```

Update these in `.env`:
- `DATABASE_URL` — your PostgreSQL connection string
- `DATA_GOV_API_KEY` — your Data.gov.in API key
- `JOB_MARKET_XLSX_PATH` — path to the Excel file

### 3. Set up PostgreSQL

Create the database:

```sql
CREATE DATABASE sih_labour;
```

Create tables using Alembic:

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 4. Run the API

```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 5. Import data

Place `indian-job-market-dataset-2025.xlsx` in `data/raw/` then:

```powershell
python -m app.ingestion.import_job_market
python -m app.ingestion.import_mgnrega
```

### 6. Run tests

```powershell
pytest
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health |
| GET | `/api/v1/meta` | Data sources and coverage |
| GET | `/api/v1/dashboard/summary` | KPI cards and summary metrics |
| GET | `/api/v1/jobs` | Search/filter job postings |
| GET | `/api/v1/skills/top` | Top skills by job count |
| GET | `/api/v1/skills/by-region` | Skills by state |
| GET | `/api/v1/mgnrega/records` | Filtered MGNREGA rows |
| GET | `/api/v1/mgnrega/indicators` | Aggregated indicator series |
| GET | `/api/v1/forecasts` | ML forecast results |
| GET | `/api/v1/ingestion/status` | Latest ingestion status |

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + router registration
│   ├── core/config.py       # Pydantic settings from .env
│   ├── db/
│   │   ├── session.py        # Engine + session factory
│   │   └── base.py           # Declarative base
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic response schemas
│   ├── api/routes/          # FastAPI route modules
│   ├── services/            # Business logic / DB queries
│   └── ingestion/           # Import scripts
├── alembic/                 # Database migrations
├── tests/
├── data/raw/                # Place Excel file here
├── requirements.txt
├── .env.example
└── .gitignore
```
