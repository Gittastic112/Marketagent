#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REQUIRED_KEYS = ("NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD")


def read_env_state(path: Path) -> dict[str, bool]:
    values: dict[str, str] = {}
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.removeprefix("export ").split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return {key: bool(values.get(key)) for key in REQUIRED_KEYS}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local-auth configuration without printing credential values."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(__file__).resolve().parents[1] / ".env",
    )
    args = parser.parse_args()

    state = read_env_state(args.env_file)
    missing = [key for key in REQUIRED_KEYS if not state[key]]
    print(
        json.dumps(
            {
                "configured": not missing,
                "missing": missing,
                "mode": "local_single_user",
                "production_ready": False,
            }
        )
    )
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
