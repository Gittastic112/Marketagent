"""Stable serialization and optional-package discovery without importing SDKs."""

import hashlib
import importlib.metadata
import json
from typing import Any

from app.services.research_lab.errors import ResearchAdapterError


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def require_package(name: str) -> str:
    version = package_version(name)
    if version is None:
        raise ResearchAdapterError(
            "ADAPTER_DEPENDENCY_MISSING",
            f"Install the locked adapters profile to use {name}.",
            503,
        )
    return version
