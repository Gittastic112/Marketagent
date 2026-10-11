"""Bounded child-process execution for the app's four PDF read operations.

This isolates resource use, not arbitrary native-code execution or filesystem
access. The local Docker runtime remains the security boundary.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
from typing import Any

MAX_INPUT_BYTES = 40 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MEMORY_BYTES = 512 * 1024 * 1024
CPU_SECONDS = 8
WALL_SECONDS = 12
WORKER_PATH = Path(__file__).resolve().parents[1] / "workers/pdf_parse_worker.py"
SLOTS = threading.BoundedSemaphore(2)
LIMIT_MESSAGE = "PDF exceeded processing limits. Select fewer pages or use a simpler text-based PDF."


class PdfJobError(ValueError):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def run_pdf_job(mode: str, content: bytes, options: dict[str, Any]) -> Any:
    if sys.platform != "linux":
        raise PdfJobError("Bounded PDF processing requires the supported Linux Docker runtime.", 503)
    if mode not in {"financial", "brief", "render", "size"} or not content.startswith(b"%PDF-"):
        raise PdfJobError("Invalid PDF processing request.")
    if len(content) > MAX_INPUT_BYTES:
        raise PdfJobError("PDF exceeds the supported size limit.", 413)
    try:
        header = json.dumps({"mode": mode, "options": options}, allow_nan=False).encode()
    except (ValueError, TypeError):
        raise PdfJobError("Invalid PDF processing options.") from None
    if len(header) >= 4096:
        raise PdfJobError("PDF processing options exceed the supported limit.")
    if not SLOTS.acquire(blocking=False):
        raise PdfJobError("PDF processing is busy. Try again shortly.", 503)
    process = None
    try:
        # A temporary regular file bounds stdout without buffering an untrusted
        # stream in the API process. The child enforces RLIMIT_FSIZE before parsing.
        with tempfile.TemporaryFile() as output:
            environment = {
                "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
                "OPENBLAS_NUM_THREADS": "1", "TZ": "UTC",
            }
            process = subprocess.Popen([sys.executable, "-s", str(WORKER_PATH)],
                stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL,
                env=environment, close_fds=True, start_new_session=True)
            try:
                process.communicate(header + b"\n" + content, timeout=WALL_SECONDS)
            except subprocess.TimeoutExpired:
                raise PdfJobError(LIMIT_MESSAGE) from None
            if process.returncode != 0 or output.tell() > MAX_OUTPUT_BYTES:
                raise PdfJobError(LIMIT_MESSAGE)
            output.seek(0)
            try:
                result = json.loads(output.read(MAX_OUTPUT_BYTES + 1))
            except (ValueError, UnicodeError):
                raise PdfJobError("PDF could not be processed safely.") from None
        if not isinstance(result, dict) or set(result) not in ({"data"}, {"error"}):
            raise PdfJobError("PDF could not be processed safely.")
        if "error" in result:
            error = result["error"]
            # Worker errors use a fixed catalog, never raw parser diagnostics.
            if not isinstance(error, dict):
                raise PdfJobError("PDF could not be processed safely.")
            code = error.get("code")
            messages = {"invalid": ("PDF could not be read. Check the file and selected pages.", 422),
                "limits": (LIMIT_MESSAGE, 422), "unavailable": ("PDF processing is unavailable.", 503),
                "too_large": ("PDF exceeds the supported size or page limit.", 413),
                "no_text": ("No usable text layer. OCR is not available; paste the text or upload a text-based PDF.", 422)}
            message, status = messages.get(code, messages["invalid"])
            raise PdfJobError(message, status)
        return result["data"]
    except OSError:
        raise PdfJobError("PDF processing is unavailable.", 503) from None
    finally:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        SLOTS.release()
