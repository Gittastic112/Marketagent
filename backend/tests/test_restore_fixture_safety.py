import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def drill(monkeypatch):
    spec = importlib.util.spec_from_file_location("restore_drill_safety", Path(__file__).resolve().parents[2] / "scripts/restore_drill_fixture.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "SessionLocal", lambda: pytest.fail("Unsafe fixture opened a database session"))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("RESTORE_DRILL_DISPOSABLE", "1")
    monkeypatch.setattr(module, "engine", SimpleNamespace(url=SimpleNamespace(host="postgres-e2e", database="marketintel_e2e")))
    return module


@pytest.mark.parametrize("action", ["seed", "clear", "verify", "write"])
@pytest.mark.parametrize("boundary", ["flag", "environment", "host", "database"])
def test_restore_fixture_rejects_non_disposable_targets_before_database_access(drill, monkeypatch, action, boundary):
    if boundary == "flag":
        monkeypatch.delenv("RESTORE_DRILL_DISPOSABLE")
    elif boundary == "environment":
        monkeypatch.setenv("APP_ENV", "local")
    else:
        setattr(drill.engine.url, boundary, "normal-app")
    with pytest.raises(RuntimeError, match="explicitly marked disposable"):
        getattr(drill, action)()


def test_restore_fixture_accepts_only_complete_disposable_identity(drill):
    drill.assert_disposable_target()
