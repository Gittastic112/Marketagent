"""One-use, bounded personal-price fetches; no application credentials in children.

This bounds resources and retries, not the SDK's remote endpoints or filesystem
access. The configured personal-use SDK is still an unofficial data source.
"""
import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading

from pydantic import TypeAdapter, ValidationError

from app.services.market_data.base import MarketDataProviderError, MarketDataRequest, MarketHistoryResult, MarketQuoteResult

WALL_SECONDS = 45
CPU_SECONDS = 10
MEMORY_BYTES = 768 * 1024 * 1024
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
WORKER_PATH = Path(__file__).resolve().parents[2] / "workers/yfinance_worker.py"
SLOTS = threading.BoundedSemaphore(2)


def failure(code: str) -> MarketDataProviderError:
    messages = {
        "PROVIDER_TIMEOUT": ("Personal-use price fetching exceeded its processing deadline.", 504),
        "PROVIDER_BUSY": ("Personal-use price fetching is busy. Try again shortly.", 503),
        "PROVIDER_UNAVAILABLE": ("Personal-use price fetching is unavailable or exceeded processing limits.", 502),
        "PROVIDER_INVALID_RESPONSE": ("Personal-use price fetching returned an invalid response.", 502),
    }
    message, status = messages.get(code, messages["PROVIDER_UNAVAILABLE"])
    return MarketDataProviderError(code=code if code in messages else "PROVIDER_UNAVAILABLE",
        message=message, status_code=status, provider="yfinance_personal")


async def run_yfinance_job(mode: str, request: MarketDataRequest, days: int = 365):
    if sys.platform != "linux":
        raise MarketDataProviderError(code="PROVIDER_UNAVAILABLE", provider="yfinance_personal",
            message="Bounded price fetching requires the supported Linux Docker runtime.", status_code=503)
    if mode not in {"quote", "history"} or not 1 <= days <= 3650:
        raise ValueError("Invalid price fetch operation or history window")
    encoded = json.dumps({"mode": mode, "request": request.model_dump(), "days": days}, allow_nan=False).encode()
    if len(encoded) > 4096:
        raise ValueError("Price request exceeds the supported size")
    if not SLOTS.acquire(blocking=False):
        raise failure("PROVIDER_BUSY")
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="market-fetch-") as cache, tempfile.TemporaryFile() as output:
            environment = {
                "PYTHONPATH": str(Path(__file__).resolve().parents[3]),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
                "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "TZ": "UTC",
                "XDG_CACHE_HOME": cache,
            }
            process = await asyncio.create_subprocess_exec(sys.executable, "-s", str(WORKER_PATH),
                stdin=asyncio.subprocess.PIPE, stdout=output, stderr=asyncio.subprocess.DEVNULL,
                env=environment, close_fds=True, start_new_session=True)
            try:
                try:
                    await asyncio.wait_for(process.communicate(encoded), timeout=WALL_SECONDS)
                except TimeoutError:
                    raise failure("PROVIDER_TIMEOUT") from None
                if process.returncode != 0 or output.tell() > MAX_OUTPUT_BYTES:
                    raise failure("PROVIDER_UNAVAILABLE")
                output.seek(0)
                try:
                    result = json.loads(output.read(MAX_OUTPUT_BYTES + 1))
                    if not isinstance(result, dict) or set(result) not in ({"data"}, {"error"}):
                        raise ValueError("Invalid envelope")
                    if "error" in result:
                        raise failure("PROVIDER_UNAVAILABLE")
                    if mode == "quote":
                        return MarketQuoteResult.model_validate(result["data"])
                    rows = result["data"]
                    if not isinstance(rows, list) or not 1 <= len(rows) <= days:
                        raise ValueError("Invalid history size")
                    return TypeAdapter(list[MarketHistoryResult]).validate_python(rows)
                except (ValueError, TypeError, ValidationError):
                    raise failure("PROVIDER_INVALID_RESPONSE") from None
            finally:
                # Cancellation must terminate the fetch, not leave a thread or
                # SDK retry running after the caller has gone away.
                if process.returncode is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    await process.wait()
    except OSError:
        raise failure("PROVIDER_UNAVAILABLE") from None
    finally:
        SLOTS.release()
