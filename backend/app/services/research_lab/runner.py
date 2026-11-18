"""Per-process concurrency, elapsed time, memory and output bounds."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading

from app.services.research_lab.common import canonical_json
from app.services.research_lab.errors import ResearchAdapterError


_slots = threading.BoundedSemaphore(2)
MAX_OUTPUT = 8 * 1024**2


def run_bounded(kind: str, data: dict, *, context: dict | None = None) -> dict:
    # Context is server controlled and is not part of the user input contract.
    raw = canonical_json(
        {"kind": kind, "input": data, "context": context or {}}
    ).encode()
    if len(raw) > 4 * 1024**2:
        raise ResearchAdapterError(
            "RESEARCH_INPUT_TOO_LARGE", "Research input exceeds 4 MiB.", 413
        )
    if not _slots.acquire(blocking=False):
        raise ResearchAdapterError(
            "RESEARCH_WORKER_BUSY",
            "Both local research workers are busy; retry later.",
            503,
        )
    try:
        backend = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory(prefix="marketagent-research-") as temp_dir:
            env = {
                "PATH": os.defpath,
                "PYTHONPATH": str(backend),
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLBACKEND": "Agg",
                "MPLCONFIGDIR": temp_dir,
                "XDG_CACHE_HOME": temp_dir,
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
                "PYTHONHASHSEED": "0",
                "LC_ALL": "C.UTF-8",
            }
            with tempfile.TemporaryFile() as output:
                process = subprocess.Popen(
                    [sys.executable, "-m", "app.services.research_lab.worker"],
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=subprocess.DEVNULL,
                    cwd=temp_dir,
                    env=env,
                    start_new_session=True,
                )
                try:
                    process.communicate(raw, timeout=40)
                except subprocess.TimeoutExpired as exc:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    raise ResearchAdapterError(
                        "RESEARCH_TIMEOUT",
                        "The research calculation exceeded its 40 second budget.",
                        504,
                    ) from exc
                if process.returncode != 0:
                    raise ResearchAdapterError(
                        "RESEARCH_WORKER_FAILED",
                        "The research worker exceeded a resource limit or failed.",
                        502,
                    )
                output.seek(0)
                response = output.read(MAX_OUTPUT + 1)
                if len(response) > MAX_OUTPUT:
                    raise ResearchAdapterError(
                        "RESEARCH_OUTPUT_TOO_LARGE",
                        "The research output exceeded its size limit.",
                        502,
                    )
            try:
                decoded = json.loads(response)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ResearchAdapterError(
                    "RESEARCH_INVALID_OUTPUT",
                    "The research worker returned invalid output.",
                    502,
                ) from exc
            if "error" in decoded:
                issue = decoded["error"]
                raise ResearchAdapterError(
                    issue["code"], issue["message"], issue["status_code"]
                )
            if not isinstance(decoded.get("result"), dict):
                raise ResearchAdapterError(
                    "RESEARCH_INVALID_OUTPUT",
                    "The research worker returned no result.",
                    502,
                )
            return decoded["result"]
    finally:
        _slots.release()
