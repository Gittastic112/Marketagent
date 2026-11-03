import pytest

from app.models import (
    Company,
    DamodaranCapexBenchmark,
    DamodaranDatasetFile,
    DamodaranMarginBenchmark,
    RawDocument,
    Source,
)
from helpers import response_data


def _company_and_benchmarks(db) -> Company:
    company = Company(
        name="Multi Segment Co",
        ticker="MIX",
        market="IN",
        country="India",
        currency="INR",
    )
    dataset = DamodaranDatasetFile(
        uploaded_filename="industryIndia.xls",
        dataset_code="industry_mix_test",
        country="India",
        source_file_type="xls",
    )
    db.add_all([company, dataset])
    db.flush()
    db.add_all(
        [
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Transportation",
                country="India",
                ebit_margin=0.20,
            ),
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Shipbuilding & Marine",
                country="India",
                ebit_margin=0.10,
            ),
            DamodaranCapexBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Transportation",
                country="India",
                sales_to_capital=1.0,
            ),
            DamodaranCapexBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Shipbuilding & Marine",
                country="India",
                sales_to_capital=2.0,
            ),
        ]
    )
    db.commit()
    return company


def _payload(first_weight: float = 60, second_weight: float = 40) -> dict:
    return {
        "basis": "revenue",
        "as_of_date": "2025-03-31",
        "notes": "User-reviewed segment revenue mix.",
        "allocations": [
            {
                "segment_name": "Ports and logistics",
                "industry_name": "Transportation",
                "weight_percent": first_weight,
            },
            {
                "segment_name": "Marine",
                "industry_name": "Shipbuilding & Marine",
                "weight_percent": second_weight,
            },
        ],
    }


def test_weighted_industry_mix_persists_and_drives_blended_autofill(client, db) -> None:
    company = _company_and_benchmarks(db)

    response = client.put(f"/companies/{company.id}/industry-allocations", json=_payload())

    assert response.status_code == 200
    mix = response_data(response)
    assert mix["basis"] == "revenue"
    assert mix["total_weight_percent"] == 100
    assert mix["primary_industry"] == "Transportation"
    assert mix["claim_type"] == "User Assumption"
    assert mix["coverage_status"] == "partial"
    assert mix["allocations"][0]["benchmark_availability"]["margins"] is True
    assert mix["allocations"][0]["benchmark_availability"]["capex"] is True
    assert [item["segment_name"] for item in mix["allocations"]] == ["Ports and logistics", "Marine"]

    db.refresh(company)
    assert company.damodaran_industry == "Transportation"
    assert response_data(client.get(f"/companies/{company.id}/industry-allocations"))["id"] == mix["id"]

    draft = response_data(
        client.post(f"/companies/{company.id}/valuation-models/autofill", json={"base_assumptions": {}})
    )
    assert draft["assumptions"]["target_operating_margin"] == 0.16
    # 60 revenue / 1.0 + 40 revenue / 2.0 requires 80 capital in total.
    assert draft["assumptions"]["sales_to_capital_ratio"] == pytest.approx(1.25)
    provenance = draft["provenance"]["target_operating_margin"]
    assert provenance["source_type"] == "industry_benchmark_blend"
    assert provenance["claim_type"] == "Estimate"
    assert provenance["industry_mix_basis"] == "revenue"
    assert provenance["aggregation_version"] == 2
    assert provenance["aggregation_methods"]["reinvestmentPriors"]["suggestedSalesToCapital"] == "revenue_weighted_harmonic_ratio"
    assert draft["source_metadata"]["industry_mix_signature"]


def test_weighted_industry_mix_can_link_company_owned_source_document(client, db) -> None:
    company = _company_and_benchmarks(db)
    source = Source(name="Annual reports", source_type="regulatory_filing")
    db.add(source)
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="Segment revenue note",
        raw_text="Segment revenue",
        content_hash="industry-mix-source",
    )
    db.add(document)
    db.commit()
    payload = _payload()
    payload["source_document_id"] = document.id

    response = client.put(f"/companies/{company.id}/industry-allocations", json=payload)

    assert response.status_code == 200
    assert response_data(response)["source_document_id"] == document.id


def test_weighted_industry_mix_rejects_invalid_total_and_unknown_taxonomy(client, db) -> None:
    company = _company_and_benchmarks(db)

    bad_total = client.put(
        f"/companies/{company.id}/industry-allocations",
        json=_payload(60, 30),
    )
    assert bad_total.status_code == 422

    unknown = _payload()
    unknown["allocations"][1]["industry_name"] = "Imaginary Industry"
    unknown_response = client.put(
        f"/companies/{company.id}/industry-allocations",
        json=unknown,
    )
    assert unknown_response.status_code == 422
    assert unknown_response.json()["errors"][0]["code"] == "INDUSTRY_MIX_INVALID"


def test_weighted_prior_does_not_renormalize_around_missing_component(client, db) -> None:
    company = _company_and_benchmarks(db)
    marine_capex = db.query(DamodaranCapexBenchmark).filter_by(
        industry_name="Shipbuilding & Marine"
    ).one()
    db.delete(marine_capex)
    db.commit()
    assert client.put(f"/companies/{company.id}/industry-allocations", json=_payload()).status_code == 200

    draft = response_data(
        client.post(f"/companies/{company.id}/valuation-models/autofill", json={"base_assumptions": {}})
    )

    assert draft["assumptions"]["sales_to_capital_ratio"] == 1.5
    assert draft["provenance"]["sales_to_capital_ratio"]["source_type"] == "generic_market_default"
    assert any(
        "reinvestmentPriors.suggestedSalesToCapital" in warning and "Marine" in warning
        for warning in draft["warnings"]
    )


def test_existing_draft_refreshes_when_mix_weights_change_but_primary_industry_does_not(client, db) -> None:
    company = _company_and_benchmarks(db)
    assert client.put(f"/companies/{company.id}/industry-allocations", json=_payload()).status_code == 200
    first = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    first_signature = first["source_metadata_json"]["industry_mix_signature"]
    assert first["assumptions_json"]["target_operating_margin"] == 0.16

    assert client.put(f"/companies/{company.id}/industry-allocations", json=_payload(70, 30)).status_code == 200
    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    assert reopened["id"] == first["id"]
    assert reopened["assumptions_json"]["target_operating_margin"] == pytest.approx(0.17)
    assert reopened["source_metadata_json"]["industry_mix_signature"] != first_signature


def test_old_blend_draft_reopens_with_correct_ratio_and_preserves_manual_inputs(client, db) -> None:
    import hashlib
    import json
    from app.models.dcf import ValuationSetupDraft
    from app.services.industry_mapping import IndustryMappingService

    company = _company_and_benchmarks(db)
    assert client.put(f"/companies/{company.id}/industry-allocations", json=_payload()).status_code == 200
    first = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    draft = db.get(ValuationSetupDraft, first["id"])
    context = IndustryMappingService.industry_mix_context(db, company.id)
    old_payload = {key: context[key] for key in ("basis", "as_of_date", "source_document_id", "allocations")}
    old_signature = hashlib.sha256(json.dumps(old_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    draft.source_metadata_json = {**draft.source_metadata_json, "industry_mix_signature": old_signature}
    draft.assumptions_json = {**draft.assumptions_json, "sales_to_capital_ratio": 1.4, "target_operating_margin": 0.23}
    draft.edited_fields_json = ["target_operating_margin"]
    draft.reviewed_fields_json = ["target_operating_margin", "sales_to_capital_ratio"]
    db.commit()

    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    assert reopened["id"] == first["id"]
    assert reopened["assumptions_json"]["sales_to_capital_ratio"] == pytest.approx(1.25)
    assert reopened["assumptions_json"]["target_operating_margin"] == 0.23
    assert "sales_to_capital_ratio" not in reopened["reviewed_fields_json"]
    assert "target_operating_margin" in reopened["reviewed_fields_json"]
    assert reopened["source_metadata_json"]["industry_mix_signature"] != old_signature
