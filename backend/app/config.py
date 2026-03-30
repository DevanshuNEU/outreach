import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Absolute path to .env — works regardless of where uvicorn is launched from
_ENV_FILE = Path(__file__).parent.parent / ".env"

# Load .env FIRST so it overrides any empty system env vars
load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""
    apollo_api_key: str = ""
    anthropic_api_key: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72
    cors_origins: str = "http://localhost:5173"
    apollo_max_contacts_per_search: int = 2
    apollo_daily_credit_limit: int = 50

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
