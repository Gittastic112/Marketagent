"""A retired connectivity command must never impersonate release acceptance."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("arguments", [
    [],
    ["--write"],
    ["--write", "--backend-url", "http://127.0.0.1:1", "--ticker", "TEST"],
])
def test_retired_command_is_unavailable_even_with_legacy_write_flags(arguments) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "verify_milestone_a.py"
    result = subprocess.run(
        [sys.executable, "-I", str(script), *arguments],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 2
    assert "Not available" in result.stderr
    assert "Data Health" in result.stderr
    assert "verify_release_baseline.sh" in result.stderr
    assert result.stdout == ""
