import importlib.util
import sys
import json
from pathlib import Path


def test_frontend_contract_manifest_matches_current_backend(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("wire_contract_check", root / "scripts/check_api_contracts.py")
    module = importlib.util.module_from_spec(spec)
    # Match normal import semantics. Pydantic registers parameterized generics
    # against the importing module even when no earlier test populated its cache.
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    assert json.loads(module.MANIFEST.read_text()) == module.contract_manifest(), (
        "Review the contract change, regenerate data/contracts/frontend-backend.json, and run frontend tests."
    )
