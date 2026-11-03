"""Mock Data subprocesses exercise actual cancellation and resource boundaries."""
import asyncio
import json
import os
import signal
import subprocess
import sys
import threading

import pytest

from app.services.market_data import yfinance_jobs as jobs
from app.services.market_data.base import MarketDataProviderError, MarketDataRequest

REQUEST = MarketDataRequest(market="US", ticker="MOCK", currency="USD")
QUOTE = {"provider_name": "yfinance_personal", "provider_symbol": "MOCK", "market": "US",
         "ticker": "MOCK", "currency": "USD", "current_price": "100"}


def worker(monkeypatch, tmp_path, source):
    path = tmp_path / "mock_worker.py"
    path.write_text(source)
    monkeypatch.setattr(jobs, "WORKER_PATH", path)


def test_worker_receives_only_public_request_and_no_application_or_proxy_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "private-database")
    monkeypatch.setenv("NEXTAUTH_SECRET", "private-session")
    monkeypatch.setenv("HTTPS_PROXY", "private-proxy")
    monkeypatch.setenv("GEMINI_API_KEY", "private-key")
    worker(monkeypatch, tmp_path, "import os,json,sys\n"
        "assert not any(k in os.environ for k in ('DATABASE_URL','NEXTAUTH_SECRET','HTTPS_PROXY','GEMINI_API_KEY'))\n"
        "request=json.load(sys.stdin)\nassert request['request']['ticker']=='MOCK'\n"
        f"print({json.dumps({'data': QUOTE})!r})\n")
    result = asyncio.run(jobs.run_yfinance_job("quote", REQUEST))
    assert result.current_price == 100 and result.ticker == "MOCK"


def test_timeout_kills_and_reaps_child_and_releases_capacity(monkeypatch, tmp_path):
    pid_file = tmp_path / "pid"
    worker(monkeypatch, tmp_path, f"import os,time\nopen({str(pid_file)!r},'w').write(str(os.getpid()))\ntime.sleep(60)\n")
    monkeypatch.setattr(jobs, "WALL_SECONDS", 0.5)
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(jobs.run_yfinance_job("quote", REQUEST))
    assert error.value.code == "PROVIDER_TIMEOUT"
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)
    assert jobs.SLOTS.acquire(blocking=False)
    jobs.SLOTS.release()


def test_async_cancellation_stops_the_sdk_instead_of_leaving_retries_running(monkeypatch, tmp_path):
    pid_file = tmp_path / "pid"
    # Publish readiness atomically: existence must mean the PID is fully written
    # before the parent deliberately kills the worker under test.
    worker(monkeypatch, tmp_path, "import os,time\nfrom pathlib import Path\n"
        f"pid_file=Path({str(pid_file)!r})\npending=pid_file.with_suffix('.pending')\n"
        "pending.write_text(str(os.getpid()))\npending.replace(pid_file)\ntime.sleep(60)\n")
    async def cancel():
        task = asyncio.create_task(jobs.run_yfinance_job("quote", REQUEST))
        async with asyncio.timeout(5):
            while not pid_file.exists():
                await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(cancel())
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def test_busy_capacity_fails_without_starting_a_child(monkeypatch):
    slots = threading.BoundedSemaphore(1)
    slots.acquire()
    monkeypatch.setattr(jobs, "SLOTS", slots)
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(jobs.run_yfinance_job("quote", REQUEST))
    assert error.value.code == "PROVIDER_BUSY"


@pytest.mark.parametrize("payload", [[], {"data": {}}, {"data": QUOTE, "extra": "bad"}, {"data": {**QUOTE, "current_price": -1}}])
def test_malformed_worker_results_are_unavailable(monkeypatch, tmp_path, payload):
    worker(monkeypatch, tmp_path, f"print({json.dumps(payload)!r})")
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(jobs.run_yfinance_job("quote", REQUEST))
    assert error.value.code == "PROVIDER_INVALID_RESPONSE"


def test_sdk_import_fits_limits_and_os_enforces_cpu_memory_and_output(tmp_path):
    env = {"PYTHONPATH": os.environ["PYTHONPATH"], "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
    prefix = "from app.workers.yfinance_worker import apply_limits; apply_limits(cpu_seconds=1); "
    imported = subprocess.run([sys.executable, "-c", "from app.workers.yfinance_worker import apply_limits; apply_limits(); import yfinance"],
        env=env, capture_output=True, timeout=15)
    assert imported.returncode == 0, imported.stderr.decode()
    cpu = subprocess.run([sys.executable, "-c", prefix + "exec('while True: pass')"], env=env, capture_output=True, timeout=5)
    assert cpu.returncode in (-signal.SIGXCPU, -signal.SIGKILL)
    memory = subprocess.run([sys.executable, "-c", prefix + "bytearray(2 * 1024**3)"], env=env, capture_output=True, timeout=5)
    assert memory.returncode != 0 and b"MemoryError" in memory.stderr
    with (tmp_path / "bounded-output").open("wb") as output:
        size = subprocess.run([sys.executable, "-c", prefix + "import sys; sys.stdout.buffer.write(b'x' * (9 * 1024**2))"],
            env=env, stdout=output, stderr=subprocess.DEVNULL, timeout=5)
    assert size.returncode != 0
    assert (tmp_path / "bounded-output").stat().st_size <= jobs.MAX_OUTPUT_BYTES


def test_public_sdk_methods_use_the_job_boundary(monkeypatch):
    from app.providers.market_data import yfinance_provider
    calls = []
    async def fetch(*args):
        calls.append(args)
        return "Mock Data result"
    monkeypatch.setattr(yfinance_provider, "run_yfinance_job", fetch)
    provider = yfinance_provider.YFinanceMarketProvider()
    assert asyncio.run(provider.get_quote(REQUEST)) == "Mock Data result"
    assert asyncio.run(provider.get_historical_prices(REQUEST, days=7)) == "Mock Data result"
    assert calls == [("quote", REQUEST), ("history", REQUEST, 7)]
