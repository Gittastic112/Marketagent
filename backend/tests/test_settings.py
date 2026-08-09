from pathlib import Path

from app.core.config import Settings, load_settings


def test_settings_load_database_url_from_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/example")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_NAME", "Test App")

    settings = load_settings(env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/example"
    assert settings.database_pool_size == 10
    assert settings.database_max_overflow == 20
    assert settings.database_pool_timeout_seconds == 10
    assert settings.app_env == "test"
    assert settings.app_name == "Test App"


def test_settings_load_sec_user_agent_from_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("SEC_USER_AGENT", "Market Intelligence Test contact@example.com")

    settings = load_settings(env_file=None)

    assert settings.sec_user_agent == "Market Intelligence Test contact@example.com"


def test_settings_load_alert_priority_threshold_from_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("ALERT_PRIORITY_THRESHOLD", "85")

    settings = load_settings(env_file=None)

    assert settings.alert_priority_threshold == 85
