import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_local_auth.py"


def test_auth_preflight_reports_names_without_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEXTAUTH_SECRET=do-not-print-secret\n"
        "LOCAL_AUTH_USERNAME=do-not-print-user\n"
        "LOCAL_AUTH_PASSWORD=\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert json.loads(result.stdout) == {
        "configured": False,
        "missing": ["LOCAL_AUTH_PASSWORD"],
        "mode": "local_single_user",
        "production_ready": False,
    }
    assert "do-not-print" not in result.stdout


def test_auth_preflight_succeeds_when_all_required_values_exist(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEXTAUTH_SECRET=secret\n"
        "LOCAL_AUTH_USERNAME=analyst\n"
        "LOCAL_AUTH_PASSWORD=password\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["configured"] is True
