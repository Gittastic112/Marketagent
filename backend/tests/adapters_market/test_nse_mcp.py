import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.providers.market_data import transport
from app.providers.market_data.nse_mcp import NSEMarketProvider, NSEMCPClient, BHAVCOPY
from app.providers.market_data.transport import WireResponse
from app.schemas.data_adapters import AdapterActionRequest, AdapterDatedQuoteRequest, AdapterHistoryRequest, MarketDataRequest
from app.services.market_data.base import MarketDataProviderError

EVIDENCE = Path(__file__).resolve().parents[3] / 'docs/workstreams/evidence/adapters-20261117/W3'
NOW = datetime(2026,11,18,2,10,tzinfo=timezone.utc)
ID = dict(market="IN",exchange="NSE",ticker="INFY",currency="INR")


def install_mcp(monkeypatch, results, *, schema_change=False):
    calls=[]
    def fetch(provider, endpoint, *, payload=None, **kwargs):
        calls.append((endpoint,payload,kwargs))
        method=payload['method']
        if method=='initialize':
            result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}}}
        elif method=='notifications/initialized':
            return WireResponse(None,'',{},NOW)
        elif method=='tools/list':
            name='nse-cmmkt-tools.json' if '/cmmkt/' in endpoint else 'nse-bhavcopy-tools.json'
            result=json.loads((EVIDENCE/name).read_text())['result']
            if schema_change:
                for tool in result['tools']:
                    if tool['name']=='get_stock_history':tool['inputSchema']['required'].append('unexpected')
        else:
            name=payload['params']['name']
            value=results[name]
            if callable(value):value=value(payload['params']['arguments'])
            if isinstance(value,Exception):raise value
            result={'isError':False,'content':[{'type':'text','text':json.dumps(value)}]}
        rpc={'jsonrpc':'2.0','id':payload['id'],'result':result}
        return WireResponse(rpc,json.dumps(rpc),{'mcp-session-id':'mock-session'},NOW)
    monkeypatch.setattr(transport,'fetch_fixed',fetch)
    return calls


def action_empty():
    return {'symbol':'INFY','actions':[],'count':0}


def history(series='EQ'):
    return {'symbol':'INFY','from_date':'2025-10-01','to_date':'2025-11-09','next_end_date':'2025-09-30',
        'data':[{'symbol':'INFY','series':'EQ','date':'2025-11-06','close':100},
                {'symbol':'INFY','series':series,'date':'2025-11-07','close':101}]}


def test_actual_captured_history_parses_eq_and_surfaces_mixed_series(monkeypatch):
    raw=json.loads((EVIDENCE/'nse-get_stock_history-sample.json').read_text())
    value=json.loads(raw['response']['result']['content'][0]['text'])
    calls=install_mcp(monkeypatch,{'get_corporate_actions':action_empty(),'get_stock_history':value})
    result=asyncio.run(NSEMarketProvider().get_history(AdapterHistoryRequest(**ID,start_date='2025-10-10',end_date='2025-11-10')))
    assert result.coverage=='partial' and len(result.gaps)==2
    assert {g.code for g in result.gaps}=={'PROVIDER_UNSUPPORTED_SERIES'}
    assert len(result.points)==18
    assert all(p.adjustment_state=='unadjusted' for p in result.points)
    assert all(c[2]['headers'].get('Mcp-Session-Id')=='mock-session' for c in calls[1:])
    args=calls[-1][1]['params']['arguments']
    assert args=={'symbol':'INFY','months':3,'endDate':'2025-11-10'}


def test_dated_price_uses_actual_history_date_and_never_bare_ltp(monkeypatch):
    calls=install_mcp(monkeypatch,{'get_corporate_actions':action_empty(),'get_stock_history':history()})
    result=asyncio.run(NSEMarketProvider().get_dated_quote(AdapterDatedQuoteRequest(**ID,requested_date='2025-11-09')))
    assert result.actual_date.isoformat()=='2025-11-07' and result.previous_session_substitution
    assert all(c[1].get('params',{}).get('name')!='get_ltp_by_date' for c in calls)


def test_dated_quote_refuses_unresolved_newer_non_eq_series(monkeypatch):
    install_mcp(monkeypatch,{'get_corporate_actions':action_empty(),'get_stock_history':history('T0')})
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(NSEMarketProvider().get_dated_quote(AdapterDatedQuoteRequest(**ID,requested_date='2025-11-09')))
    assert exc.value.code=='PROVIDER_DATE_UNRESOLVED'


def test_tool_schema_change_is_visible_before_history_call(monkeypatch):
    calls=install_mcp(monkeypatch,{'get_corporate_actions':action_empty(),'get_stock_history':history()},schema_change=True)
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(NSEMarketProvider().get_history(AdapterHistoryRequest(**ID,start_date='2025-11-01',end_date='2025-11-09')))
    assert exc.value.code=='PROVIDER_TOOL_SCHEMA_CHANGED'
    assert not any(c[1].get('params',{}).get('name')=='get_stock_history' for c in calls)


def test_captured_current_quote_source_timestamp_is_not_refresh_timestamp(monkeypatch):
    raw=json.loads((EVIDENCE/'nse-cm_get_stock_quote-detail-sample.json').read_text())
    value=json.loads(raw['response']['result']['content'][0]['text'])
    install_mcp(monkeypatch,{'cm_get_stock_quote':value})
    result=asyncio.run(NSEMarketProvider().get_quote(MarketDataRequest(**ID)))
    assert result.source_timestamp.isoformat()=='2026-11-17T10:30:29+00:00'
    assert result.observed_at==NOW and result.price_type=='delayed'
    assert result.current_price==1130


def test_captured_action_preserves_description_without_guessing_money(monkeypatch):
    raw=json.loads((EVIDENCE/'nse-get_corporate_actions-detail-sample.json').read_text())
    value=json.loads(raw['response']['result']['content'][0]['text'])
    install_mcp(monkeypatch,{'get_corporate_actions':value})
    result=asyncio.run(NSEMarketProvider().get_actions(AdapterActionRequest(**ID,start_date='2025-10-01',end_date='2025-11-10')))
    assert result.actions[0].action_type=='dividend'
    assert result.actions[0].cash_amount is None and result.actions[0].publication_time is None
    assert result.actions[0].source_response_hash


def test_nse_partial_second_window_failure_retains_first_window(monkeypatch):
    def window(args):
        if args['endDate']=='2025-11-09':
            return {**history(),'from_date':'2025-11-01','next_end_date':'2025-10-31'}
        from app.providers.market_data.transport import provider_error
        raise provider_error('nse_mcp','PROVIDER_RATE_LIMITED','Mock Data rate limit',retryable=True)
    install_mcp(monkeypatch,{'get_corporate_actions':action_empty(),'get_stock_history':window})
    result=asyncio.run(NSEMarketProvider().get_history(AdapterHistoryRequest(**ID,start_date='2025-10-01',end_date='2025-11-09')))
    assert result.coverage=='partial' and len(result.points)==2
    assert result.gaps[0].code=='PROVIDER_RATE_LIMITED'
