from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_ROOT / 'cabapp.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = 'CabApp API'
    environment: str = 'development'
    debug: bool = False
    api_v1_prefix: str = '/api/v1'
    database_url: str = DEFAULT_DATABASE_URL
    auto_migrate: bool = True
    jwt_secret_key: str = 'change-this-development-secret-before-production'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    otp_expiry_minutes: int = 10
    firebase_credentials_path: str | None = None
    google_maps_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / '.env', extra='ignore')


@lru_cache
def get_settings() -> Settings:
    return Settings()
