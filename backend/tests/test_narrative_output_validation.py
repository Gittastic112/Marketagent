"""Untrusted provider JSON must be typed before a narrative result is successful."""
import json

import pytest
from sqlalchemy import func, select

from app.models.ai import AiOutput
from app.models.dcf import DcfAssumptionSet
from app.providers.base import AIProviderResult
from app.providers.mock_provider import MockAIProvider
from test_assumption_version_integrity import saved


def valid_estimates():
    return {
        "target_operating_margin": 0,
        "target_operating_margin_reason": "Mock Data private response marker",
        "revenue_growth_years": {"1": 0, "2": -0.1},
        "revenue_growth_reason": "Mock Data growth estimate",
        "sales_to_capital_ratio": 2,
        "sales_to_capital_reason": "Mock Data reinvestment estimate",
        "terminal_growth_rate": 0,
        "terminal_growth_reason": "Mock Data terminal estimate",
    }


def post_estimates(client, db_session, monkeypatch, provider_output):
    model, row = saved(client, db_session)
    provider = MockAIProvider()
    monkeypatch.setattr(provider, "generate_structured_response", lambda *_: AIProviderResult(
        output_text=json.dumps(provider_output), model_name="mock-model",
        confidence_label="low", limitations="Mock Data provider fixture",
    ))
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    count = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    response = client.post(f"/valuation/{model.id}/scenarios/Base/ai/narrative-to-numbers", json={
        "privacy_disclosure_version": "v1", "assumption_set_id": row["id"],
        "assumptions_updated_at": row["updated_at"], "narrative_text": "Mock Data private narrative marker",
    })
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == count
    db_session.expire_all()
    stored = db_session.get(DcfAssumptionSet, row["id"])
    assert stored.story_text is None
    assert stored.target_operating_margin == row["target_operating_margin"]
    assert stored.revenue_growth_years_json == row["revenue_growth_years_json"]
    return response, row


@pytest.mark.parametrize("case", [
    "list", "null", "missing_reason", "object_reason", "list_reason", "number_reason",
    "empty_reason", "long_reason", "string_rate", "boolean_rate", "null_rate", "nan_rate",
    "infinite_reinvestment", "zero_reinvestment", "negative_reinvestment", "growth_list",
    "empty_growth", "string_growth_rate", "boolean_growth_rate", "invalid_year", "year_31",
    "terminal_out_of_bounds", "unknown_field",
])
def test_invalid_narrative_estimates_fail_safely_and_are_audited(client, db_session, monkeypatch, caplog, case):
    payload = valid_estimates()
    changes = {
        "object_reason": ("target_operating_margin_reason", {"private": "Mock Data private response marker"}),
        "list_reason": ("revenue_growth_reason", ["Mock Data private response marker"]),
        "number_reason": ("sales_to_capital_reason", 42),
        "empty_reason": ("terminal_growth_reason", ""),
        "long_reason": ("terminal_growth_reason", "x" * 2001),
        "string_rate": ("target_operating_margin", "0.2"),
        "boolean_rate": ("target_operating_margin", True),
        "null_rate": ("target_operating_margin", None),
        "nan_rate": ("target_operating_margin", float("nan")),
        "infinite_reinvestment": ("sales_to_capital_ratio", float("inf")),
        "zero_reinvestment": ("sales_to_capital_ratio", 0),
        "negative_reinvestment": ("sales_to_capital_ratio", -1),
        "growth_list": ("revenue_growth_years", [0.1]),
        "empty_growth": ("revenue_growth_years", {}),
        "string_growth_rate": ("revenue_growth_years", {"1": "0.1"}),
        "boolean_growth_rate": ("revenue_growth_years", {"1": False}),
        "invalid_year": ("revenue_growth_years", {"year_1": 0.1}),
        "year_31": ("revenue_growth_years", {"31": 0.1}),
        "terminal_out_of_bounds": ("terminal_growth_rate", 1),
        "unknown_field": ("unexpected", "Mock Data private response marker"),
    }
    if case == "list":
        payload = []
    elif case == "null":
        payload = None
    elif case == "missing_reason":
        payload.pop("revenue_growth_reason")
    else:
        field, value = changes[case]
        payload[field] = value

    response, row = post_estimates(client, db_session, monkeypatch, payload)
    assert response.status_code == 502, response.text
    assert response.json()["errors"][0]["code"] == "AI_PROVIDER_FAILED"
    outputs = db_session.scalars(select(AiOutput)).all()
    assert len(outputs) == 1
    output = outputs[0]
    assert output.execution_status == "failed" and output.failure_code == "AI_PROVIDER_FAILED"
    assert output.output_text == "" and output.human_review_status == "pending"
    assert output.reference_id == row["id"]
    assert output.evaluation_json["valuation_basis"]["assumption_set_id"] == row["id"]
    assert len(output.input_hash) == 64
    public_evidence = response.text + (output.limitations or "") + caplog.text
    assert "private response marker" not in public_evidence
    assert "private narrative marker" not in public_evidence


def test_valid_narrative_estimates_preserve_zero_values_and_saved_basis(client, db_session, monkeypatch):
    payload = valid_estimates()
    response, row = post_estimates(client, db_session, monkeypatch, payload)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert {key: data[key] for key in payload} == payload
    assert data["target_operating_margin"] == data["terminal_growth_rate"] == data["revenue_growth_years"]["1"] == 0
    assert data["evidence"]["assumption_set_id"] == row["id"]
    assert data["evidence"]["basis_verified"] and data["evidence"]["is_current"]
    output = db_session.scalar(select(AiOutput))
    assert output.execution_status == "success" and output.failure_code is None
    assert json.loads(output.output_text) == payload
