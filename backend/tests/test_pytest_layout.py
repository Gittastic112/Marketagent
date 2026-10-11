import ast
from pathlib import Path


def test_backend_root_debug_scripts_do_not_shadow_suite_modules() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    suite_names = {path.name for path in (backend_root / "tests").glob("test_*.py")}
    root_names = {path.name for path in backend_root.glob("test_*.py")}

    shadowed_names = sorted(suite_names & root_names)

    assert shadowed_names == [], (
        "Root-level debug scripts shadow real pytest modules: "
        f"{', '.join(shadowed_names)}. Move or rename the debug script."
    )


def test_backend_manual_scripts_do_not_define_pytest_tests() -> None:
    scripts_root = Path(__file__).resolve().parents[1] / "scripts"
    violations: list[str] = []

    for path in sorted(scripts_root.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
                "test_"
            ):
                violations.append(f"{path.name}:{node.name}")

    assert violations == [], (
        "Manual backend scripts are being collected as pytest tests: "
        f"{', '.join(violations)}. Rename their test_* functions or move the "
        "checks into backend/tests/."
    )
