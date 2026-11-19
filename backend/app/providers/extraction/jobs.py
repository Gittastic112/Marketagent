"""Single-use extraction workers with OS resource and outbound-network limits."""
from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading

from app.providers.research_sources.errors import SourceAdapterError

PACKAGES = {"edgartools": "edgartools", "camelot": "camelot-py", "docling": "docling", "marker": "marker-pdf"}
MAX_INPUT = 40 * 1024 * 1024
MAX_OUTPUT = 12 * 1024 * 1024
WALL_SECONDS = 60
SLOTS = threading.BoundedSemaphore(1)


def dependency_version(adapter: str, python_executable: str | None = None) -> str | None:
    if python_executable:
        executable = Path(python_executable)
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK) or adapter not in PACKAGES:
            return None
        try:
            probe = subprocess.run([str(executable), "-I", "-s", "-c",
                "import importlib.metadata; print(importlib.metadata.version(" + repr(PACKAGES[adapter]) + "))"],
                capture_output=True, timeout=5, text=True, env={"PATH": "/usr/bin:/bin"})
            value = probe.stdout.strip()
            return value if probe.returncode == 0 and 0 < len(value) < 100 else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    try:
        return importlib.metadata.version(PACKAGES[adapter])
    except (KeyError, importlib.metadata.PackageNotFoundError):
        return None


def _marker_versions(python_executable: str | None = None) -> dict[str, str | None]:
    """Inspect the configured worker, without importing models or installing them."""
    names = ("marker-pdf", "surya-ocr", "Pillow", "filelock")
    if python_executable:
        executable = Path(python_executable)
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
            return {}
        script = "import importlib.metadata as m,json\nv={}\nfor name in " + repr(names) + ":\n try: v[name]=m.version(name)\n except m.PackageNotFoundError: v[name]=None\nprint(json.dumps(v))"
        try:
            probe = subprocess.run([str(executable), "-I", "-s", "-c", script],
                capture_output=True, timeout=5, text=True, env={"PATH": "/usr/bin:/bin"})
            if probe.returncode or len(probe.stdout) > 4096:
                return {}
            value = json.loads(probe.stdout)
            return value if isinstance(value, dict) and set(value) == set(names) else {}
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return {}
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def extraction_dependency_conflict(adapter: str, python_executable: str | None = None) -> str | None:
    if adapter != "marker":
        return None
    from packaging.version import InvalidVersion, Version

    versions = _marker_versions(python_executable)
    try:
        if not versions or any(value is None for value in versions.values()):
            return "The complete Marker dependency stack could not be verified."
        parsed = {name: Version(value) for name, value in versions.items()}
    except (InvalidVersion, TypeError):
        return "The Marker dependency versions could not be verified."
    if parsed["Pillow"] < Version("13.0.0") or parsed["filelock"] < Version("4.2.12"):
        return "Marker is blocked by the approved dependency floor: Pillow 13.0.0 and filelock 4.2.12 are required."
    if parsed["marker-pdf"] <= Version("2.2.0") or parsed["surya-ocr"] < Version("0.24.0"):
        return "The published Marker 2.2.0 / Surya 0.23 dependency requirements conflict with the approved Pillow/filelock versions."
    return None


def run_extraction(adapter: str, content: bytes, *, pages: list[int] | None = None,
                   model_dir: str | None = None, options: dict | None = None,
                   python_executable: str | None = None) -> dict:
    if adapter not in PACKAGES or not content or len(content) > MAX_INPUT:
        raise SourceAdapterError("EXTRACTION_INPUT_INVALID", "Invalid or oversized extraction input.")
    version = dependency_version(adapter, python_executable)
    if not version:
        raise SourceAdapterError("EXTRACTION_DEPENDENCY_MISSING", f"The optional {adapter} dependency is not installed.", 503)
    conflict = extraction_dependency_conflict(adapter, python_executable)
    if conflict:
        raise SourceAdapterError("EXTRACTION_DEPENDENCY_CONFLICT", conflict, 503)
    if sys.platform != "linux":
        raise SourceAdapterError("EXTRACTION_ISOLATION_UNAVAILABLE", "Bounded extraction requires Linux.", 503)
    artifact_path = None
    if adapter in {"docling", "marker"}:
        if not model_dir or not Path(model_dir).is_dir():
            raise SourceAdapterError("EXTRACTION_MODELS_MISSING", "Local extraction model artifacts are not configured.", 503)
        artifact_path = str(Path(model_dir).resolve())
    if adapter != "edgartools" and (not content.startswith(b"%PDF-") or not pages or len(pages) > 20 or any(p < 1 or p > 1000 for p in pages)):
        raise SourceAdapterError("EXTRACTION_INPUT_INVALID", "Select at most 20 valid PDF pages.")
    if not SLOTS.acquire(blocking=False):
        raise SourceAdapterError("EXTRACTION_BUSY", "The extraction worker is busy.", 503, retryable=True)
    process = None
    try:
        header = json.dumps({"adapter": adapter, "pages": pages, "options": options or {}, "model_dir": artifact_path}).encode()
        if len(header) > 4096:
            raise SourceAdapterError("EXTRACTION_INPUT_INVALID", "Extraction options exceed the supported limit.")
        with tempfile.TemporaryDirectory(prefix="marketagent-extract-") as directory, tempfile.TemporaryFile() as output:
            environment = {"PYTHONPATH": str(Path(__file__).resolve().parents[3]),
                "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1", "TOKENIZERS_PARALLELISM": "false", "TZ": "UTC", "PATH": "/usr/bin:/bin",
                "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "TORCH_DEVICE": "cpu",
                "EDGAR_LOCAL_DATA_DIR": directory, "XDG_CACHE_HOME": artifact_path or directory,
                "HF_HOME": artifact_path or directory}
            process = subprocess.Popen([python_executable or sys.executable, "-s", "-m", "app.providers.extraction.worker"],
                stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL, env=environment,
                cwd=directory, close_fds=True, start_new_session=True)
            try:
                process.communicate(header + b"\n" + content, timeout=WALL_SECONDS)
            except subprocess.TimeoutExpired:
                raise SourceAdapterError("EXTRACTION_LIMIT", "Extraction exceeded its time budget; select fewer pages.", 422) from None
            if process.returncode or output.tell() > MAX_OUTPUT:
                raise SourceAdapterError("EXTRACTION_LIMIT", "Extraction exceeded its resource budget or failed safely.", 422)
            output.seek(0)
            result = json.loads(output.read(MAX_OUTPUT + 1))
        if not isinstance(result, dict):
            raise ValueError
        if "error" in result:
            code = result["error"]
            catalog = {"isolation": ("EXTRACTION_ISOLATION_UNAVAILABLE", "Outbound network isolation is unavailable.", 503),
                "dependency": ("EXTRACTION_DEPENDENCY_MISSING", "An extraction dependency or local model artifact is unavailable.", 503),
                "invalid": ("EXTRACTION_FAILED", "The selected extractor could not parse this source within its contract.", 422),
                "limits": ("EXTRACTION_LIMIT", "Extraction exceeded its resource budget.", 422)}
            raise SourceAdapterError(*catalog.get(code, catalog["invalid"]))
        if not isinstance(result.get("data"), dict):
            raise ValueError
        data = result["data"]
        if adapter != "edgartools":
            from app.providers.extraction.pdf import map_pdf_tables
            data = map_pdf_tables(data, adapter=adapter, period_type=(options or {}).get("period_type", "unknown"))
        return {**data, "dependency_version": version}
    except SourceAdapterError:
        raise
    except Exception:
        raise SourceAdapterError("EXTRACTION_FAILED", "Extraction could not be completed safely.", 422) from None
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        SLOTS.release()
