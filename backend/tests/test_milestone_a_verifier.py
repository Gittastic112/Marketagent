import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "verify_milestone_a.py"
SPEC = importlib.util.spec_from_file_location("verify_milestone_a", SCRIPT_PATH)
assert SPEC is not None
verify_milestone_a = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_milestone_a)

find_record = verify_milestone_a.find_record
join_url = verify_milestone_a.join_url
milestone_status = verify_milestone_a.milestone_status
get_or_create_company = verify_milestone_a.get_or_create_company


def test_join_url_handles_slashes() -> None:
    assert join_url("http://127.0.0.1:8000/", "/health") == "http://127.0.0.1:8000/health"


def test_find_record_matches_all_criteria() -> None:
    records = [
        {"id": 1, "name": "SEC EDGAR", "source_type": "sec"},
        {"id": 2, "name": "Example RSS", "source_type": "rss"},
    ]

    assert find_record(records, name="Example RSS", source_type="rss") == records[1]
    assert find_record(records, name="Example RSS", source_type="sec") is None


def test_milestone_status_requires_three_rss_feeds_for_live_verification() -> None:
    status = milestone_status(rss_feed_count=2, write_enabled=True)

    assert status["rss_live_feeds"] == "needs_3_feeds"


def test_milestone_status_skips_writes_in_dry_run() -> None:
    status = milestone_status(rss_feed_count=3, write_enabled=False)

    assert status["database_writes"] == "dry_run"
    assert status["rss_live_feeds"] == "dry_run"


def test_get_or_create_company_updates_existing_company_without_cik(monkeypatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    def fake_request_json(method: str, base_url: str, path: str, payload: dict | None = None, timeout: int = 30):
        calls.append((method, path, payload))
        if method == "GET" and path == "/companies":
            return [{"id": 2, "ticker": "AAPL", "name": "Apple", "cik": None}]
        if method == "GET" and path == "/companies/lookup?ticker=AAPL":
            return {"ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193"}
        if method == "PATCH" and path == "/companies/2":
            return {"id": 2, "ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193"}
        raise AssertionError(f"Unexpected request {method} {path}")

    monkeypatch.setattr(verify_milestone_a, "request_json", fake_request_json)

    company = get_or_create_company("http://backend", "aapl")

    assert company["cik"] == "0000320193"
    assert calls[-1] == (
        "PATCH",
        "/companies/2",
        {"name": "Apple Inc.", "cik": "0000320193", "ticker": "AAPL"},
    )
