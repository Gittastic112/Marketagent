from types import SimpleNamespace

from sqlalchemy import select

from app.models import Company, MarketPrice, ProcessingRun
from app.services import provider_connectivity as probes
from app.services.market_data.base import MarketDataRequest


def test_public_identity_probe_is_audited_without_creating_coverage(db, monkeypatch):
    monkeypatch.setattr(probes, "get_settings", lambda: SimpleNamespace(sec_user_agent="Mock Data test@example.invalid"))
    monkeypatch.setattr(probes, "lookup_cik_for_ticker", lambda *_a, **_k: "0000000001")
    monkeypatch.setattr(probes, "fetch_recent_sec_filing_metadata", lambda *_a, **_k: ["Mock Data filing"])
    result = probes.probe_public_provider(db, "sec", request=MarketDataRequest(market="US", ticker="MOCK"))
    assert result["status"] == "success" and result["evidence"]["filing_count"] == 1
    run = db.scalar(select(ProcessingRun))
    assert run.finished_at and run.run_type == "provider_connectivity_probe"
    assert run.created_count == 0
    assert not db.scalars(select(Company)).all() and not db.scalars(select(MarketPrice)).all()


def test_unconfigured_probe_and_provider_exception_are_visible_and_sanitized(db, monkeypatch):
    monkeypatch.setattr(probes, "get_settings", lambda: SimpleNamespace(fred_api_key=None))
    result = probes.probe_public_provider(db, "fred")
    assert result["status"] == "failed" and result["failure_code"] == "PROVIDER_NOT_CONFIGURED"
    monkeypatch.setattr(probes, "get_settings", lambda: SimpleNamespace(fred_api_key="private-key"))
    def fail(*_a, **_k):
        raise RuntimeError("private-key raw provider response")
    monkeypatch.setattr(probes.FredProvider, "fetch_observations", fail)
    result = probes.probe_public_provider(db, "fred")
    assert result["failure_code"] == "PROVIDER_PROBE_FAILED"
    assert "private-key" not in str(result)
    assert "private-key" not in str([run.metadata_json for run in db.scalars(select(ProcessingRun))])
