import asyncio
from datetime import datetime, timezone
import json

import pytest

from app.providers.calendars.exchange_calendar import get_exchange_schedule
from app.providers.identity.openfigi import OpenFIGIProvider
from app.providers.market_data import transport
from app.providers.market_data.transport import WireResponse
from app.schemas.data_adapters import CalendarScheduleRequest, IdentityMappingRequest
from app.services.market_data.base import MarketDataProviderError


def test_openfigi_preserves_ambiguity_and_delisted_request(monkeypatch):
    seen={}
    def fetch(provider,endpoint,**kwargs):
        seen.update(kwargs)
        value=[{'data':[{'figi':'FIGI1','ticker':'MOCK.A','shareClassFIGI':'SHARE1'},
                        {'figi':'FIGI2','ticker':'MOCK.B','shareClassFIGI':'SHARE2'}]}]
        return WireResponse(value,json.dumps(value),{},datetime.now(timezone.utc))
    monkeypatch.setattr(transport,'fetch_fixed',fetch)
    result=asyncio.run(OpenFIGIProvider('secret').map_identity(IdentityMappingRequest(id_type='TICKER',
        id_value='MOCK',include_unlisted_equities=True)))
    assert result.resolution=='ambiguous' and len(result.candidates)==2
    assert seen['payload'][0]['includeUnlistedEquities'] is True
    assert seen['headers']['X-OPENFIGI-APIKEY']=='secret'
    assert result.candidates[0].share_class_figi != result.candidates[1].share_class_figi


def test_calendar_real_library_early_close_and_dst():
    result=get_exchange_schedule(CalendarScheduleRequest(exchange='XNYS',start_date='2025-07-01',end_date='2025-07-07'))
    by_day={s.date.isoformat():s for s in result.sessions}
    assert '2025-07-04' not in by_day
    assert by_day['2025-07-03'].closes_at.hour==17
    winter=get_exchange_schedule(CalendarScheduleRequest(exchange='XNYS',start_date='2025-01-06',end_date='2025-01-06'))
    assert winter.sessions[0].opens_at.hour==14 and by_day['2025-07-01'].opens_at.hour==13
    assert result.library_version=='5.6.1'


def test_calendar_outside_coverage_rejected():
    with pytest.raises(MarketDataProviderError) as exc:
        get_exchange_schedule(CalendarScheduleRequest(exchange='XNSE',start_date='2027-01-01',end_date='2027-01-05'))
    assert exc.value.code=='CALENDAR_OUTSIDE_COVERAGE'


def test_weekend_override_is_explicit_sourced_and_hashed():
    request=CalendarScheduleRequest(exchange='XNSE',start_date='2023-11-12',end_date='2023-11-12',overrides=[{
        'date':'2023-11-12','opens_at':'2023-11-12T18:15:00+05:30','closes_at':'2023-11-12T19:15:00+05:30',
        'source_url':'https://www.nseindia.com/mock-announcement','reason':'Mock Data override to verify weekend behavior'}])
    result=get_exchange_schedule(request)
    assert len(result.sessions)==1 and result.sessions[0].source=='user_source_override'
    empty=get_exchange_schedule(request.model_copy(update={'overrides':[]}))
    assert empty.sessions==[] and empty.override_hash!=result.override_hash


def test_override_local_date_mismatch_fails():
    request=CalendarScheduleRequest(exchange='XNSE',start_date='2025-01-06',end_date='2025-01-06',overrides=[{
        'date':'2025-01-06','opens_at':'2025-01-05T01:00:00Z','closes_at':'2025-01-05T02:00:00Z',
        'source_url':'https://www.nseindia.com/mock-announcement','reason':'Mock Data'}])
    with pytest.raises(MarketDataProviderError) as exc:
        get_exchange_schedule(request)
    assert exc.value.code=='CALENDAR_OVERRIDE_DATE_MISMATCH'
