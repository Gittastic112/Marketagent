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


def test_market_probe_preserves_valid_empty_history_without_inventing_dates(db,monkeypatch):
    from app.services.market_data.base import MarketQuoteResult
    class Provider:
        provider_name='mock_official'
        async def get_quote(self,request):
            return MarketQuoteResult(provider_name=self.provider_name,provider_symbol='MOCK',market='US',
                ticker='MOCK',currency='USD',current_price=10)
        async def get_historical_prices(self,request,days):
            return []
    monkeypatch.setattr(probes,'get_settings',lambda:SimpleNamespace())
    monkeypatch.setattr(probes,'get_market_data_provider',lambda:Provider())
    result=probes.probe_public_provider(db,'market',request=MarketDataRequest(market='US',ticker='MOCK',currency='USD'))
    assert result['status']=='success' and result['evidence']['history_empty']
    assert result['evidence']['first_history_date'] is None and result['evidence']['last_history_date'] is None
    assert not db.scalars(select(MarketPrice)).all()
