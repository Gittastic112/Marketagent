from datetime import date

from app.models.damodaran import DamodaranDatasetFile
from app.models.real_options import IndustryVolatilityBenchmark
from helpers import response_data


def _version(db, *, active: bool, source_hash: str) -> DamodaranDatasetFile:
    version = DamodaranDatasetFile(
        uploaded_filename="optvarIndia.xls",
        dataset_code="volatility",
        country="India",
        source_file_type="xls",
        source_sha256=source_hash,
        source_byte_size=100,
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path="raw/datasets/optvarIndia(1).xls",
        import_kind="typed",
        is_active=active,
        row_count=1,
    )
    db.add(version)
    db.flush()
    return version


def _benchmark(db, version: DamodaranDatasetFile, *, equity_volatility: float) -> None:
    db.add(
        IndustryVolatilityBenchmark(
            dataset_file_id=version.id,
            country="India",
            data_date=date(2026, 1, 5),
            industry_name="Utility (General)",
            number_of_firms=0,
            equity_standard_deviation=equity_volatility,
            firm_value_standard_deviation=None,
            equity_value_weight=None,
            debt_value_weight=None,
            assumed_debt_to_equity_vol_ratio=0.40,
            assumed_debt_equity_correlation=0.50,
            source_file="optvarIndia.xls",
        )
    )


def test_volatility_api_uses_active_version_and_preserves_zero_and_nulls(client, db) -> None:
    old_version = _version(db, active=False, source_hash="old-hash")
    active_version = _version(db, active=True, source_hash="active-hash")
    _benchmark(db, old_version, equity_volatility=0.99)
    _benchmark(db, active_version, equity_volatility=0.0)
    db.commit()

    response = client.get(
        "/api/valuation/options/volatility",
        params={"country": "India", "industry": "Utility (General)"},
    )

    assert response.status_code == 200
    payload = response_data(response)
    assert payload["datasetVersionId"] == active_version.id
    assert payload["claimType"] == "Source Summary"
    assert payload["numberOfFirms"] == 0
    assert payload["equityStandardDeviation"] == 0.0
    assert payload["firmValueStandardDeviation"] is None
    assert payload["equityValueWeight"] is None
    assert payload["debtValueWeight"] is None
    assert payload["assumptions"] == {
        "debtToEquityVolatilityRatio": 0.40,
        "debtEquityCorrelation": 0.50,
    }
    assert payload["sourceFile"] == "optvarIndia.xls"
    assert payload["sourceSha256"] == "active-hash"
    assert payload["sourceAsOf"] == "2026-01-05"
    assert payload["dateConfidence"] == "high"
    assert payload["canonicalSourcePath"] == "raw/datasets/optvarIndia(1).xls"
    assert response.json()["meta"]["is_mock"] is False


def test_volatility_api_returns_not_found_instead_of_generic_fallback(client) -> None:
    response = client.get(
        "/api/valuation/options/volatility",
        params={"country": "India", "industry": "Not Loaded"},
    )

    assert response.status_code == 404
    assert response.json()["data"] is None
    assert response.json()["errors"][0]["code"] == "VOLATILITY_BENCHMARK_NOT_FOUND"


def test_real_option_canonical_routes_and_legacy_volatility_alias(client, db) -> None:
    version = _version(db, active=True, source_hash="active-hash")
    _benchmark(db, version, equity_volatility=0.25)
    db.commit()

    legacy = client.get(
        "/volatility",
        params={"country": "India", "industry": "Utility (General)"},
    )
    assert legacy.status_code == 200

    eligibility = client.post(
        "/api/valuation/options/eligibility",
        json={
            "option_type": "call",
            "has_underlying_asset": True,
            "has_finite_life": True,
            "has_clear_exercise_price": True,
            "has_asymmetric_payoff": True,
            "has_exclusivity": True,
            "can_estimate_volatility": True,
            "can_estimate_underlying_value": True,
        },
    )
    assert eligibility.status_code == 200

    calculation = client.post(
        "/api/valuation/options/calculate",
        json={
            "option_type": "call",
            "underlying_asset_value": 100,
            "exercise_price": 100,
            "option_life_years": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.20,
        },
    )
    assert calculation.status_code == 200
    assert calculation.json()["meta"]["source"] == "experimental_legacy_custom_option"
    assert calculation.json()["meta"]["confidence"] == "low"
    assert any("Experimental" in note for note in response_data(calculation)["warnings"])
    assert any("not verified" in note for note in response_data(eligibility)["warnings"])

    alias = client.post("/calculate", json={
        "option_type": "call", "underlying_asset_value": 100, "exercise_price": 100,
        "option_life_years": 1, "risk_free_rate": .05, "volatility": .20,
    })
    assert response_data(alias) == response_data(calculation)
    assert alias.json()["meta"]["source"] == calculation.json()["meta"]["source"]

    documented_paths = client.get("/openapi.json").json()["paths"]
    assert "/api/valuation/options/volatility" in documented_paths
    assert "/api/valuation/options/eligibility" in documented_paths
    assert "/api/valuation/options/calculate" in documented_paths
    assert "/volatility" not in documented_paths
    assert "/eligibility" not in documented_paths
    assert "/calculate" not in documented_paths
    assert documented_paths["/api/valuation/options/calculate"]["post"]["deprecated"]
