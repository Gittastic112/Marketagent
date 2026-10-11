from datetime import date, timedelta

from sqlalchemy import select

from app.models.macro import MacroObservation, MacroSeries
from app.models.market_regime_input import MarketRegimeInput
from app.services.market_regime_macro_provider import normalize_nfci


def _nfci_series(db, *, observation_date: date, value: float) -> tuple[MacroSeries, MacroObservation]:
    series = MacroSeries(
        name="NFCI",
        description="National Financial Conditions Index",
        units="Index",
        frequency="Weekly",
        provider_name="FRED",
        source_url="https://fred.stlouisfed.org/series/NFCI",
    )
    db.add(series)
    db.flush()
    observation = MacroObservation(
        series_id=series.id,
        date_recorded=observation_date,
        value=value,
    )
    db.add(observation)
    db.commit()
    return series, observation


def test_nfci_normalization_is_bounded_and_directionally_explicit() -> None:
    assert normalize_nfci(-2.5) == 100
    assert normalize_nfci(-0.4) == 20
    assert normalize_nfci(0) == 0
    assert normalize_nfci(0.4) == -20
    assert normalize_nfci(2.5) == -100
    for value in (float("nan"), float("inf"), float("-inf")):
        try:
            normalize_nfci(value)
        except ValueError:
            pass
        else:
            raise AssertionError("Non-finite NFCI values must be rejected")


def test_nfci_preview_blocks_missing_persisted_series(client) -> None:
    response = client.get("/market-regime/providers/fred/macro/preview")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["can_apply"] is False
    assert body["data"]["claim_type"] == "Calculation"
    assert "Import the FRED NFCI series" in body["data"]["blockers"][0]
    assert body["meta"]["source"] == "FRED"
    assert body["meta"]["confidence"] == "none"


def test_nfci_preview_requires_verified_fred_provenance(client, db) -> None:
    series = MacroSeries(name="NFCI", provider_name="manual")
    db.add(series)
    db.flush()
    db.add(MacroObservation(series_id=series.id, date_recorded=date.today(), value=-0.2))
    db.commit()

    preview = client.get("/market-regime/providers/fred/macro/preview").json()["data"]

    assert preview["can_apply"] is False
    assert "lacks verified FRED provenance" in preview["blockers"][0]


def test_nfci_preview_ignores_future_observations(client, db) -> None:
    _nfci_series(db, observation_date=date.today() + timedelta(days=1), value=-0.2)

    preview = client.get("/market-regime/providers/fred/macro/preview").json()["data"]

    assert preview["can_apply"] is False
    assert preview["observation_id"] is None
    assert "on or before the target date" in preview["blockers"][-1]


def test_nfci_apply_links_exact_observation_and_is_idempotent(client, db) -> None:
    series, observation = _nfci_series(db, observation_date=date.today(), value=-0.42)

    first = client.post("/market-regime/providers/fred/macro/apply")
    second = client.post("/market-regime/providers/fred/macro/apply")

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    first_data = first.json()["data"]
    second_data = second.json()["data"]
    assert first_data["macro_series_id"] == series.id
    assert first_data["observation_id"] == observation.id
    assert first_data["normalized_value"] == 21
    assert first_data["created"] is True
    assert second_data["created"] is False
    assert second_data["applied_input_id"] == first_data["applied_input_id"]
    inputs = list(db.scalars(select(MarketRegimeInput)))
    assert len(inputs) == 1
    assert inputs[0].source_record_type == "macro_observation"
    assert inputs[0].source_record_id == observation.id
    assert inputs[0].input_type == "provider"

    current = client.get("/market-regime/current").json()["data"]
    macro_source = next(item for item in current["input_sources"] if item["metric_name"] == "macro")
    assert macro_source["claim_type"] == "Calculation"
    assert macro_source["evidence_state"] == "linked_record"
    assert macro_source["source_record_id"] == observation.id


def test_nfci_stale_observation_remains_explicit(client, db) -> None:
    _nfci_series(db, observation_date=date.today() - timedelta(days=32), value=0.2)

    preview = client.get("/market-regime/providers/fred/macro/preview").json()
    applied = client.post("/market-regime/providers/fred/macro/apply").json()

    assert preview["data"]["can_apply"] is True
    assert preview["data"]["is_stale"] is True
    assert preview["meta"]["is_stale"] is True
    assert "Applying it will produce a stale regime state" in preview["data"]["warnings"][0]
    assert applied["data"]["created"] is True
    assert applied["meta"]["is_stale"] is True


def test_nfci_apply_returns_stable_blocked_error(client) -> None:
    response = client.post("/market-regime/providers/fred/macro/apply")

    assert response.status_code == 409
    error = response.json()["errors"][0]
    assert error["code"] == "REGIME_PROVIDER_INPUT_BLOCKED"
    assert error["provider"] == "FRED"
