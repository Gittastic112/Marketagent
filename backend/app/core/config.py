from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    database_url: str
    app_env: str = "local"
    app_name: str = "Market Intelligence Engine"

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_settings(env_file: str | Path | None = DEFAULT_ENV_FILE) -> Settings:
    return Settings(_env_file=env_file)


@lru_cache
def get_settings() -> Settings:
    return load_settings()
