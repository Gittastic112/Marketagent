"""Keep extracted contracts independent and legacy imports compatible."""
import ast
from collections import Counter
import importlib
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("module_name", [
    "valuation_inputs", "valuation_outputs", "valuation", "portfolio", "common",
    "ai", "brief", "companies", "evidence", "financials", "health", "ingestion",
    "market", "operations", "option_calculations", "research",
])
def test_legacy_valuation_schema_exports_are_identical(module_name):
    from app.api import schemas as legacy

    module = importlib.import_module(f"app.schemas.{module_name}")
    if module_name == "common":
        assert legacy.ApiResponse[int] is module.ApiResponse[int]
    for name, value in vars(module).items():
        # Pydantic also registers generated generic specializations under names
        # such as ApiResponse[AlertRead]; those are not declared public exports.
        if name.isidentifier() and isinstance(value, type) and value.__module__ == module.__name__:
            assert getattr(legacy, name) is value, name


def test_calculation_contracts_do_not_load_http_or_service_layers():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import sys; import app.schemas.valuation_inputs; import app.schemas.valuation_outputs; import app.schemas.real_options; import app.schemas.portfolio; "
            "import app.schemas.common; "
            "assert not any(n.startswith(('app.api', 'app.services', 'app.models')) for n in sys.modules)"
        )],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_every_domain_contract_is_independent_of_http_and_persistence():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import importlib, pkgutil, sys; import app.schemas; "
            "[importlib.import_module(m.name) for m in pkgutil.iter_modules(app.schemas.__path__, 'app.schemas.')]; "
            "assert not any(n.startswith(('app.api', 'app.services', 'app.models', 'sqlalchemy', 'fastapi')) for n in sys.modules)"
        )], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_legacy_schema_facade_contains_only_compatibility_imports():
    source = Path(__file__).resolve().parents[1] / "app/api/schemas.py"
    for node in ast.parse(source.read_text()).body:
        assert isinstance(node, (ast.Expr, ast.ImportFrom))
        if isinstance(node, ast.ImportFrom):
            assert node.module.startswith("app.schemas.")


def test_extracted_peer_calculations_and_autofill_provenance_are_pure():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import sys; import app.services.peer_diagnostics; import app.services.assumption_provenance; "
            "import app.services.damodaran_workbook; "
            "assert not any(n.startswith(('app.api', 'app.models', 'sqlalchemy', 'fastapi')) for n in sys.modules)"
        )], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_market_provider_construction_has_one_authoritative_factory():
    root = Path(__file__).resolve().parents[1] / "app"
    owners = [path.relative_to(root).as_posix() for path in root.rglob("*.py")
              if any(isinstance(node, ast.FunctionDef) and node.name == "get_market_data_provider"
                     for node in ast.parse(path.read_text()).body)]
    assert owners == ["services/market_data/factory.py"]


def test_error_handling_does_not_load_domain_services_or_models():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import sys; import app.api.errors; "
            "assert 'app.api.schemas' not in sys.modules; "
            "assert not any(n.startswith(('app.services', 'app.models')) for n in sys.modules)"
        )], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_envelope_only_consumers_do_not_load_legacy_domain_contracts():
    root = Path(__file__).resolve().parents[1] / "app"
    for path in (root / "api").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module == "app.api.schemas":
                names = {alias.name for alias in node.names}
                assert not names <= {"ApiResponse", "ApiMeta", "ApiErrorDetail"}, str(path)


def test_valuation_engines_do_not_import_the_http_schema_facade():
    root = Path(__file__).resolve().parents[1] / "app" / "services"
    modules = (
        "fcfe_ddm_engine", "relative_valuation_service", "quick_valuation",
        "valuation_setup_draft", "reverse_dcf_engine", "scenario_engine", "diagnostics_engine",
        "assumption_versions", "reverse_dcf_service", "saved_real_options",
    )
    for name in modules:
        tree = ast.parse((root / f"{name}.py").read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert "app.api.schemas" not in imports, name


def test_schema_modules_do_not_silently_overwrite_class_names():
    root = Path(__file__).resolve().parents[1] / "app"
    for path in [root / "api" / "schemas.py", *sorted((root / "schemas").glob("*.py"))]:
        names = Counter(node.name for node in ast.parse(path.read_text()).body if isinstance(node, ast.ClassDef))
        assert all(count == 1 for count in names.values()), str(path)


def test_stored_and_chart_financial_metrics_keep_distinct_wire_fields():
    from app.api.schemas import FinancialMetricRead, FinancialStatementPeriodRead, StoredFinancialMetricRead

    assert set(FinancialMetricRead.model_fields) == {"metric_name", "value", "unit"}
    assert set(StoredFinancialMetricRead.model_fields) == {
        "metric_name", "value", "unit", "period_id", "id", "created_at", "updated_at",
    }
    assert FinancialStatementPeriodRead.model_fields["metrics"].annotation == list[StoredFinancialMetricRead]
