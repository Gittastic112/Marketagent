from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    database_url: str
    database_pool_size: int = Field(default=10, gt=0)
    database_max_overflow: int = Field(default=20, ge=0)
    database_pool_timeout_seconds: int = Field(default=10, gt=0)
    app_env: str = "local"
    app_name: str = "Market Intelligence Engine"
    sec_user_agent: str = "Market Intelligence Engine local research app"
    alert_priority_threshold: int = 60
    fred_api_key: str | None = None
    encryption_key: str | None = None
    market_data_provider: str = "alphavantage"
    alpha_vantage_api_key: str | None = None
    fmp_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]
    nextauth_secret: str | None = None
    log_level: str = "INFO"
    gemini_api_key: str | None = None
    ai_demo_mode: bool = False
    ai_privacy_disclosure_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("sec_user_agent")
    @classmethod
    def validate_sec_user_agent(cls, v: str) -> str:
        if v == "Market Intelligence Engine local research app" or "@" not in v:
            raise ValueError("SEC_USER_AGENT environment variable must be configured in .env with a valid email format (e.g. 'YourName email@example.com') to avoid rate limits and comply with SEC terms of service.")
        return v


def load_settings(env_file: str | Path | None = DEFAULT_ENV_FILE) -> Settings:
    return Settings(_env_file=env_file)


@lru_cache
def get_settings() -> Settings:
    return load_settings()
