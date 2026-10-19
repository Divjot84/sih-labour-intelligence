"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings resolved from .env or process environment."""

    APP_ENV: str = "development"
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/sih_labour"
    )
    DATA_GOV_API_KEY: str = ""
    DATA_GOV_MGNREGA_RESOURCE_ID: str = "ee03643a-ee4c-48c2-ac30-9f2ff26ab722"
    JOB_MARKET_XLSX_PATH: str = "./data/raw/indian-job-market-dataset-2025.xlsx"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
