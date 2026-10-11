from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest

from app.services import pdf_jobs


FIXTURE = Path(__file__).parent / "fixtures" / "financial_statement_table.pdf"


def test_parser_subprocess_preserves_real_text_and_geometry_without_credentials(monkeypatch):
    original = subprocess.Popen
    launches = []

    def spawn(*args, **kwargs):
        launches.append(kwargs)
        assert "DATABASE_URL" not in kwargs["env"]
        assert "NEXTAUTH_SECRET" not in kwargs["env"]
        assert "GEMINI_API_KEY" not in kwargs["env"]
        assert kwargs["start_new_session"] is True
        assert kwargs.get("shell", False) is False
        return original(*args, **kwargs)

    monkeypatch.setattr(pdf_jobs.subprocess, "Popen", spawn)
    parsed = pdf_jobs.run_pdf_job("financial", FIXTURE.read_bytes(), {"page_numbers": [1], "period_type": "annual"})
    assert parsed["page_count"] == 1
    assert parsed["scanned_pages"] == [1]
    assert parsed["candidates"]
    assert parsed["candidates"][0]["source_locator_json"]["page"] == 1
    assert len(launches) == 1


def test_timeout_kills_and_reaps_the_parser_and_releases_slot(monkeypatch, tmp_path):
    worker = tmp_path / "sleep_worker.py"
    worker.write_text("import time\ntime.sleep(60)\n")
    monkeypatch.setattr(pdf_jobs, "WORKER_PATH", worker)
    monkeypatch.setattr(pdf_jobs, "WALL_SECONDS", 0.1)
    original = subprocess.Popen
    processes = []

    def spawn(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(pdf_jobs.subprocess, "Popen", spawn)
    started = time.monotonic()
    for _ in range(3):
        with pytest.raises(pdf_jobs.PdfJobError, match="processing limits"):
            pdf_jobs.run_pdf_job("size", FIXTURE.read_bytes(), {"page_number": 1})
    assert time.monotonic() - started < 5
    assert all(process.poll() == -signal.SIGKILL for process in processes)


def test_busy_parser_rejects_immediately_without_spawning(monkeypatch):
    slots = threading.BoundedSemaphore(1)
    slots.acquire()
    monkeypatch.setattr(pdf_jobs, "SLOTS", slots)
    monkeypatch.setattr(pdf_jobs.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Busy job spawned"))
    with pytest.raises(pdf_jobs.PdfJobError) as caught:
        pdf_jobs.run_pdf_job("size", FIXTURE.read_bytes(), {"page_number": 1})
    assert caught.value.status_code == 503


def test_malformed_oversized_and_unknown_jobs_never_spawn(monkeypatch):
    monkeypatch.setattr(pdf_jobs, "MAX_INPUT_BYTES", 16)
    monkeypatch.setattr(pdf_jobs.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Invalid job spawned"))
    for mode, data in (("size", b"%PDF-" + b"x" * 20), ("size", b"not PDF"), ("arbitrary_module", b"%PDF-")):
        with pytest.raises(pdf_jobs.PdfJobError):
            pdf_jobs.run_pdf_job(mode, data, {})


@pytest.mark.parametrize("output", ["not-json", '{"unexpected":"private data"}', "x" * 200])
def test_worker_output_is_bounded_and_untrusted(monkeypatch, tmp_path, output):
    worker = tmp_path / "invalid_worker.py"
    worker.write_text(f"import sys\nsys.stdin.buffer.read()\nprint({output!r})\n")
    monkeypatch.setattr(pdf_jobs, "WORKER_PATH", worker)
    monkeypatch.setattr(pdf_jobs, "MAX_OUTPUT_BYTES", 100)
    with pytest.raises(pdf_jobs.PdfJobError) as caught:
        pdf_jobs.run_pdf_job("size", FIXTURE.read_bytes(), {"page_number": 1})
    assert "private data" not in str(caught.value)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux is the supported Docker parser runtime")
def test_os_cpu_and_memory_limits_are_effective():
    environment = {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    cpu = subprocess.run([sys.executable, "-c", "from app.workers.pdf_parse_worker import apply_limits; apply_limits(cpu_seconds=1); exec('while True: pass')"],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    assert cpu.returncode in (-signal.SIGXCPU, -signal.SIGKILL)
    memory = subprocess.run([sys.executable, "-c", "from app.workers.pdf_parse_worker import apply_limits; apply_limits(memory_bytes=96*1024*1024); bytearray(256*1024*1024)"],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    assert memory.returncode != 0 and b"MemoryError" in memory.stderr


def test_unsupported_runtime_fails_closed(monkeypatch):
    monkeypatch.setattr(pdf_jobs.sys, "platform", "unsupported")
    with pytest.raises(pdf_jobs.PdfJobError) as caught:
        pdf_jobs.run_pdf_job("size", FIXTURE.read_bytes(), {"page_number": 1})
    assert caught.value.status_code == 503
