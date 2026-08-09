from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import CountryMarketStats, DamodaranPricingBenchmark
from app.services.relative_valuation import (
    FinancialsInput,
    RelativeValuationBenchmarkService,
    RelativeValuationRequest,
    RelativeValuationRunService,
)


def _add_source(
    db: Session,
    code: str,
    *,
    active: bool = True,
    industry: str = "Advertising",
    **metrics,
) -> DamodaranDatasetFile:
    version = DamodaranDatasetFile(
        uploaded_filename=f"{code}India.xls",
        dataset_code=code,
        country="India",
        source_file_type="xls",
        source_sha256=(code * 64)[:64],
        source_byte_size=100,
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path=f"raw/datasets/{code}India.xls",
        import_kind="typed",
        is_active=active,
        row_count=1,
    )
    db.add(version)
    db.flush()
    db.add(
        DamodaranPricingBenchmark(
            dataset_file_id=version.id,
            industry_name=industry,
            country="India",
            number_of_firms=24,
            **metrics,
        )
    )
    db.commit()
    return version


def _seed_pricing_sources(db: Session) -> dict[str, DamodaranDatasetFile]:
    _add_source(db, "pe", active=False, pe_current=999.0)
    return {
        "pe": _add_source(db, "pe", pe_current=10.0, percent_money_losing=0.2),
        "pbv": _add_source(db, "pbv", pbv_ratio=2.0, roe=0.15, roic=0.12),
        "ps": _add_source(db, "ps", ps_ratio=3.0, ev_to_sales=4.0, net_margin=0.1),
        "vebitda": _add_source(
            db,
            "vebitda",
            ev_to_ebitda_positive_ebitda=5.0,
            ev_to_ebitda_all=6.0,
            ev_to_ebit_positive_ebitda=7.0,
            ev_to_ebit_all=8.0,
        ),
    }


def _add_country_stats(
    db: Session,
    *,
    active: bool,
    current_pe: float,
) -> DamodaranDatasetFile:
    version = DamodaranDatasetFile(
        uploaded_filename="countrystats.xls",
        dataset_code="countrystats",
        country="Global",
        source_file_type="xls",
        source_sha256=("active" if active else "inactive").ljust(64, "0"),
        source_as_of="2026-01-05",
        date_confidence="high",
        canonical_source_path="raw/datasets/countrystats.xls",
        import_kind="typed",
        is_active=active,
        row_count=1,
    )
    db.add(version)
    db.flush()
    db.add(
        CountryMarketStats(
            dataset_file_id=version.id,
            country="India",
            firm_count=4520,
            median_current_pe=current_pe,
        )
    )
    db.commit()
    return version


def test_active_pricing_bundle_assembles_each_source_without_sparse_first_row(db_session) -> None:
    versions = _seed_pricing_sources(db_session)
    benchmark = RelativeValuationBenchmarkService.get_industry_benchmark(
        db_session, "India", "Advertising"
    )
    assert benchmark is not None
    assert set(benchmark.sources) == {"pe", "pbv", "ps", "vebitda"}
    assert benchmark.row("pe").pe_current == 10.0
    assert benchmark.sources["pe"].version.id == versions["pe"].id
    assert benchmark.as_dict()["metrics"]["roe"] == 0.15
    assert len(benchmark.as_dict()["sources"]) == 4


def test_relative_valuation_uses_method_specific_rows_and_provenance(db_session) -> None:
    versions = _seed_pricing_sources(db_session)
    result = RelativeValuationRunService.run_valuation(
        db_session,
        RelativeValuationRequest(
            country="India",
            industryName="Advertising",
            financials=FinancialsInput(
                revenue=100.0,
                ebitda=20.0,
                ebit=15.0,
                netIncome=10.0,
                bookEquity=50.0,
                debt=10.0,
                cash=5.0,
                dilutedShares=10.0,
            ),
            methods=["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"],
        ),
    )
    values = {item["methodId"]: item for item in result["relativeValues"]}
    assert {method: values[method]["benchmarkMultiple"] for method in values} == {
        "pe": 10.0,
        "pbv": 2.0,
        "ps": 3.0,
        "ev_sales": 4.0,
        "ev_ebitda": 5.0,
        "ev_ebit": 7.0,
    }
    assert values["pe"]["source"]["datasetVersionId"] == versions["pe"].id
    assert values["ev_sales"]["source"]["sourceCode"] == "ps"
    assert values["ev_ebitda"]["source"]["sourceCode"] == "vebitda"
    assert all(item["claimType"] == "Calculation" for item in values.values())
    assert result["unavailableMethods"] == []
    assert len(result["benchmarkSources"]) == 4


def test_relative_valuation_reports_requested_but_unavailable_methods(db_session) -> None:
    _add_source(db_session, "pe", pe_current=10.0)
    result = RelativeValuationRunService.run_valuation(
        db_session,
        RelativeValuationRequest(
            country="India",
            industryName="Advertising",
            financials=FinancialsInput(netIncome=10.0, dilutedShares=10.0),
            methods=["pe", "pbv"],
        ),
    )
    assert [item["methodId"] for item in result["relativeValues"]] == ["pe"]
    assert result["unavailableMethods"] == [
        {"method": "pbv", "reason": "Active pbv benchmark is unavailable"}
    ]


def test_relative_valuation_preserves_zero_instead_of_falling_back(db_session) -> None:
    _add_source(
        db_session,
        "vebitda",
        ev_to_ebitda_positive_ebitda=0.0,
        ev_to_ebitda_all=9.0,
    )
    result = RelativeValuationRunService.run_valuation(
        db_session,
        RelativeValuationRequest(
            country="India",
            industryName="Advertising",
            financials=FinancialsInput(ebitda=10.0, debt=0.0, cash=0.0, dilutedShares=10.0),
            methods=["ev_ebitda"],
        ),
    )
    assert result["relativeValues"][0]["benchmarkMultiple"] == 0.0


def test_relative_valuation_api_exposes_only_active_pricing_sources(client, db_session) -> None:
    versions = _seed_pricing_sources(db_session)
    countries = client.get("/api/valuation/relative/countries")
    assert countries.status_code == 200
    assert countries.json()["data"] == ["India"]

    industries = client.get("/api/valuation/relative/countries/India/industries")
    assert industries.status_code == 200
    assert industries.json()["data"] == ["Advertising"]

    benchmark = client.get(
        "/api/valuation/relative/countries/India/industries/Advertising"
    )
    assert benchmark.status_code == 200
    payload = benchmark.json()["data"]
    assert payload["metrics"]["pe_current"] == 10.0
    assert {source["datasetVersionId"] for source in payload["sources"]} == {
        version.id for version in versions.values()
    }
    assert benchmark.json()["meta"]["source"] == "Damodaran India pricing workbooks"

    run = client.post(
        "/api/valuation/relative/run",
        json={
            "country": "India",
            "industryName": "Advertising",
            "financials": {
                "revenue": 100.0,
                "ebitda": 20.0,
                "ebit": 15.0,
                "netIncome": 10.0,
                "bookEquity": 50.0,
                "debt": 10.0,
                "cash": 5.0,
                "dilutedShares": 10.0,
            },
            "methods": ["pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit"],
        },
    )
    assert run.status_code == 200
    assert len(run.json()["data"]["relativeValues"]) == 6
    assert len(run.json()["data"]["benchmarkSources"]) == 4

    legacy = client.get("/relative-valuation/countries")
    assert legacy.status_code == 200
    assert legacy.json()["data"] == ["India"]


def test_country_stats_api_uses_only_active_version_and_exposes_provenance(
    client,
    db_session,
) -> None:
    _add_country_stats(db_session, active=False, current_pe=999.0)
    active = _add_country_stats(db_session, active=True, current_pe=25.59375)

    stats = RelativeValuationBenchmarkService.get_country_stats(db_session, "India")
    assert stats is not None
    assert stats.row.median_current_pe == 25.59375
    assert stats.version.id == active.id

    response = client.get("/api/valuation/relative/countries/India/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["median_current_pe"] == 25.59375
    assert payload["data"]["source"]["datasetVersionId"] == active.id
    assert payload["data"]["source"]["claimType"] == "Fact"
    assert payload["meta"]["confidence"] == "high"
    assert payload["meta"]["warnings"] == []
