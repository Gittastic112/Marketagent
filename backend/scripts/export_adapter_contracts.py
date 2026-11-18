"""Export/check new adapter OpenAPI contracts without database/provider access."""

import argparse
import json
from pathlib import Path


def build_contract() -> dict:
    from app.main import app

    original = app.openapi()
    paths = {
        path: operations
        for path, operations in original["paths"].items()
        if path.startswith(
            ("/api/research-lab/", "/api/data-adapters/", "/api/source-adapters")
        )
        or (path.startswith("/api/companies/") and "/source-adapters/" in path)
    }
    pending, included = [], {}

    def collect(value):
        if isinstance(value, dict):
            reference = value.get("$ref", "")
            if reference.startswith("#/components/schemas/"):
                pending.append(reference.removeprefix("#/components/schemas/"))
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(paths)
    while pending:
        name = pending.pop()
        if name not in included:
            included[name] = original["components"]["schemas"][name]
            collect(included[name])
    return {
        "openapi": original["openapi"],
        "info": {"title": "Marketagent adapter API", "version": "1"},
        "paths": paths,
        "components": {"schemas": included},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    encoded = (
        json.dumps(build_contract(), sort_keys=True, indent=2, ensure_ascii=False)
        + "\n"
    )
    if args.check:
        if not args.output.is_file() or args.output.read_text() != encoded:
            raise SystemExit(
                "Adapter OpenAPI snapshot is stale. Regenerate contracts and TypeScript types."
            )
        print("Adapter OpenAPI snapshot matches the registered backend.")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
        print(f"Exported adapter OpenAPI snapshot to {args.output}.")


if __name__ == "__main__":
    main()
