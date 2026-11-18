"""Reject direct-pin drift and runtime/test version mismatches without network."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def pins(text: str, *, require_hashes: bool = False) -> dict[str, str]:
    result = {}
    logical = text.replace("\\\n", " ")
    for line in logical.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r ", "-c ")):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([^\s;]+)(.*)", line
        )
        if not match:
            raise ValueError("Unsupported dependency declaration")
        name, version, tail = match.groups()
        name = re.sub(r"[-_.]+", "-", name).lower()
        if name in result or (
            require_hashes
            and not re.fullmatch(r"(?:\s+--hash=sha256:[0-9a-f]{64})+\s*", tail)
        ):
            raise ValueError(f"Invalid or unhashed lock entry: {name}")
        result[name] = version
    return result


def main() -> None:
    runtime = pins(
        (ROOT / "backend/requirements.lock").read_text(), require_hashes=True
    )
    test = pins(
        (ROOT / "backend/requirements-test.lock").read_text(), require_hashes=True
    )
    for manifest, lock in (
        ("requirements.txt", runtime),
        ("requirements-test.txt", test),
    ):
        for name, version in pins((ROOT / "backend" / manifest).read_text()).items():
            if lock.get(name) != version:
                raise ValueError(f"Regenerate dependency lock for {name}")
    if any(test.get(name) != version for name, version in runtime.items()):
        raise ValueError("Test lock must preserve every runtime dependency version")
    profiles = {}
    for profile in ("adapters", "extraction", "ocr"):
        manifest = ROOT / "backend" / f"requirements-{profile}.txt"
        lock = pins(manifest.with_suffix(".lock").read_text(), require_hashes=True)
        for name, version in pins(manifest.read_text()).items():
            if lock.get(name) != version:
                raise ValueError(f"Regenerate {profile} dependency lock for {name}")
        if profile != "ocr" and any(
            lock[name] != version for name, version in runtime.items() if name in lock
        ):
            raise ValueError(
                f"The {profile} profile must preserve overlapping runtime versions"
            )
        profiles[profile] = lock
    if any(
        profiles["adapters"][name] != version
        for name, version in profiles["extraction"].items()
        if name in profiles["adapters"]
    ):
        raise ValueError(
            "Scientific and table profiles must agree on shared dependencies"
        )
    print(
        f"Dependency locks consistent: {len(runtime)} runtime and {len(test)} test packages."
    )
    print(
        "Optional profiles consistent: "
        + ", ".join(f"{name}={len(lock)}" for name, lock in profiles.items())
        + "; OCR uses a separate interpreter."
    )


if __name__ == "__main__":
    main()
