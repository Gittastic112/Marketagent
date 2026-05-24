from pathlib import Path

from app.core.config import load_settings


def test_settings_load_database_url_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/example\n"
        "APP_ENV=test\n"
        "APP_NAME=Test App\n",
        encoding="utf-8",
    )

    settings = load_settings(env_file)

    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/example"
    assert settings.app_env == "test"
    assert settings.app_name == "Test App"
