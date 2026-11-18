import asyncio
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.api.dependencies import get_current_user
from app.api.errors import PublicApiError, http_exception_handler
from app.api.routers.data_adapters import router
from app.db.session import get_db
from app.models.processing_run import ProcessingRun
from app.models.raw_document import RawDocument
from app.providers.market_data.transport import CapturedResponse, provider_error
from app.schemas.data_adapters import AdapterHistoryRequest, AdapterHistoryResult, MarketHistoryResult
from app.services.market_data import adapter_workflow
from app.services.market_data.base import MarketDataProviderError
from app.services.processing_run_visibility import visible_processing_run_filter


class MockProvider:
    def __init__(self):
        self.transport=SimpleNamespace(request_count=1)
        self.captures=[]
    async def get_history(self, request):
        value={'symbol':'MOCK','description':'Mock Data','rows':[{'date':'2025-01-02','close':10}]}
        self.captures=[CapturedResponse('https://financialmodelingprep.com/stable/historical-price-eod/full',
            {'params':{'symbol':'MOCK'}},value,json.dumps(value),datetime.now(timezone.utc))]
        return AdapterHistoryResult(requested_start=request.start_date,requested_end=request.end_date,coverage='complete',
            points=[MarketHistoryResult(provider_name='fmp',provider_symbol='MOCK',market='US',ticker='MOCK',currency='USD',
                date='2025-01-02',close_price=10,adjustment_state='adjusted')])


def request():
    return AdapterHistoryRequest(market='US',ticker='MOCK',start_date='2025-01-02',end_date='2025-01-03')


def test_workflow_preserves_response_deduplicates_and_keeps_observation_history(db,monkeypatch):
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',lambda _:MockProvider())
    first=asyncio.run(adapter_workflow.execute_data_adapter(db,user_id='owner-a',provider='fmp',operation='history',request=request()))
    document=db.get(RawDocument,first.source_document_ids[0]);observed=document.ingested_at
    second=asyncio.run(adapter_workflow.execute_data_adapter(db,user_id='owner-a',provider='fmp',operation='history',request=request()))
    assert first.source_document_ids==second.source_document_ids
    assert db.query(RawDocument).count()==1 and db.get(RawDocument,document.id).ingested_at==observed
    assert document.published_at is None
    assert db.get(ProcessingRun,second.processing_run_id).skipped_duplicate_count==1
    assert list(db.scalars(select(ProcessingRun).where(visible_processing_run_filter('owner-b'))))==[]
    assert len(list(db.scalars(select(ProcessingRun).where(visible_processing_run_filter('owner-a')))))==2


def test_configuration_failure_has_owned_sanitized_finished_run(db,monkeypatch):
    def missing(_):raise provider_error('massive','PROVIDER_NOT_CONFIGURED','Massive not configured.',status=503)
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',missing)
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(adapter_workflow.execute_data_adapter(db,user_id='owner-a',provider='massive',operation='history',request=request()))
    run=db.get(ProcessingRun,exc.value.processing_run_id)
    assert run.status=='failed' and run.finished_at and run.metadata_json['user_id']=='owner-a'
    assert db.query(RawDocument).count()==0


def test_cancelled_provider_run_is_terminal_and_does_not_write_source(db,monkeypatch):
    class Cancel(MockProvider):
        async def get_history(self,request):raise asyncio.CancelledError()
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',lambda _:Cancel())
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(adapter_workflow.execute_data_adapter(db,user_id='owner',provider='fmp',operation='history',request=request()))
    run=db.scalar(select(ProcessingRun))
    assert run.status=='failed' and run.error_details_json['code']=='ADAPTER_CANCELLED'
    assert db.query(RawDocument).count()==0


def test_router_requires_auth_before_external_operation(db,monkeypatch):
    called=[]
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',lambda _:called.append(True))
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_db]=lambda:db
    with TestClient(app) as client:
        result=client.post('/api/data-adapters/fmp/history',json=request().model_dump(mode='json'))
    assert result.status_code==401 and not called and db.query(ProcessingRun).count()==0


def test_router_typed_envelope_and_owned_audit(db,monkeypatch):
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',lambda _:MockProvider())
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user]=lambda:{'id':'owner-a'}
    with TestClient(app) as client:
        response=client.post('/api/data-adapters/fmp/history',json=request().model_dump(mode='json'))
    assert response.status_code==200,response.text
    payload=response.json()
    assert payload['meta']['source']=='fmp' and not payload['meta']['is_mock']
    assert payload['data']['result']['coverage']=='complete'
    assert payload['data']['source_document_ids']
    assert payload['data']['result']['points'][0]['close_price']=='10'


def test_router_unsupported_capability_is_explicit_and_audited(db,monkeypatch):
    monkeypatch.setattr(adapter_workflow,'get_market_data_provider',lambda _:MockProvider())
    app=FastAPI();app.include_router(router)
    app.add_exception_handler(PublicApiError,http_exception_handler)
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user]=lambda:{'id':'owner-a'}
    with TestClient(app) as client:
        response=client.post('/api/data-adapters/fmp/reference',json={'market':'US','ticker':'MOCK'})
    assert response.status_code==422
    assert response.json()['errors'][0]['code']=='PROVIDER_CAPABILITY_UNSUPPORTED'
    assert response.json()['errors'][0]['processing_run_id']
