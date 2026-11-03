import json

import pytest
from sqlalchemy import select

from app.models.processing_run import ProcessingRun
from app.providers.ai_provider import GeminiRequestError
from app.providers.base import AIProviderResult
from app.services.ai_provider_probe import probe_gemini


def test_probe_records_success_without_private_data(db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-flash")
    monkeypatch.setattr("app.services.ai_provider_probe.GeminiAIProvider.check_connection",
                        lambda self: AIProviderResult(self.model_name, "OK", "Connectivity only", "none"))
    result = probe_gemini(db)
    run = db.get(ProcessingRun, result["processing_run_id"])
    assert result["status"] == "success"
    assert run.fetched_count == 1 and run.finished_at is not None
    assert run.metadata_json["model"] == "gemini-test-flash"
    assert run.metadata_json["external_data_classes"] == ["fixed_connectivity_prompt"]
    assert "test-key" not in json.dumps(run.metadata_json)


@pytest.mark.parametrize("status,code", [(404,"AI_MODEL_UNAVAILABLE"),(403,"AI_ACCESS_DENIED"),(429,"AI_RATE_LIMITED")])
def test_probe_records_safe_failures(db, monkeypatch, status, code):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    def fail(self):
        raise GeminiRequestError("private raw body test-key", status_code=status)
    monkeypatch.setattr("app.services.ai_provider_probe.GeminiAIProvider.check_connection", fail)
    result = probe_gemini(db)
    run = db.get(ProcessingRun, result["processing_run_id"])
    assert result["status"] == "failed" and result["failure_code"] == code
    assert run.error_count == 1 and run.finished_at is not None
    assert "test-key" not in json.dumps(run.error_details_json)


def test_unconfigured_probe_never_calls_provider(db, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    def unexpected(self):
        pytest.fail("An unconfigured check must not call the network")
    monkeypatch.setattr("app.services.ai_provider_probe.GeminiAIProvider.check_connection", unexpected)
    result = probe_gemini(db)
    assert result["failure_code"] == "AI_PROVIDER_NOT_CONFIGURED"
    run = db.scalar(select(ProcessingRun))
    assert run.metadata_json["external_data_classes"] == []
