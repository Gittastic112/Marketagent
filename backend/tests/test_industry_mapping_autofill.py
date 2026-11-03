import pytest
from app.models import Company
from helpers import response_data

def test_industry_mapping_autofill_provenance(client, db) -> None:
    company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        market="US",
        currency="USD",
        country="United States",
        damodaran_industry="Computers/Peripherals"
    )
    db.add(company)
    db.commit()

    response = client.post(f"/companies/{company.id}/valuation-models/autofill", json={"base_assumptions": {}})
    assert response.status_code == 200

    draft = response_data(response)
    assert "provenance" in draft
    assert draft["provenance"]["scenario"]["label"] == "Structural Default"
    assert draft["provenance"]["terminal_growth_rate"]["label"] == "Missing risk_free_rate"
    assert draft["source_metadata"]["promotion_ready"] is False
    assert "starting_revenue" in draft["source_metadata"]["placeholder_fields"]
    assert draft["assumptions"]["starting_revenue"] == 0.0
    assert draft["provenance"]["starting_revenue"]["source_type"] == "missing_actual_default"
    assert draft["provenance"]["starting_revenue"]["label"] == "[PLACEHOLDER] Requires Manual Entry"
    assert draft["provenance"]["starting_revenue"]["requires_review"] is True
