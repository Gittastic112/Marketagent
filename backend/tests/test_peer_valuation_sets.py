from datetime import date, timedelta
import csv
from io import StringIO
import pytest

from app.models import (
    Company,
    PeerValuationMemberRecord,
    PeerValuationRevisionMemberRecord,
    PeerValuationRevisionTargetProfile,
    PeerValuationSet,
    PeerValuationTargetProfile,
)
from app.models.user import User
from app.api.response_contracts import build_response_contract_inventory
from app.api.route_security import build_route_security_inventory
from app.main import app
from helpers import response_data, response_errors


@pytest.mark.parametrize("state,blocker", [
    ("archived", "archived"),
    ("draft", "review_required"),
    ("missing", "receipt_missing"),
    ("next_day", "receipt_stale"),
    ("sparse", "insufficient_method_coverage"),
])
def test_peer_eligibility_exposes_precise_blockers(client, db_session, state, blocker):
    from app.services.peer_valuation_sets import calculate_peer_diagnostics, peer_set_calculation_eligibility, peer_set_members
    target = _company(db_session, "ELIGIBILITY")
    created = _create_peer_set(client, target.id)
    reviewed = response_data(client.post(
        f"/api/valuation/relative/peer-sets/{created['id']}/review", json=_review_payload(created),
    ))
    record = db_session.get(PeerValuationSet, reviewed["id"])
    if state == "archived":
        record.is_active = False
    elif state == "draft":
        record.review_status = "draft"
    elif state == "missing":
        record.review_warning_codes_json = None
    elif state == "sparse":
        for member in record.member_records[1:]:
            member.included = False
    diagnostics = calculate_peer_diagnostics(
        peer_set_members(record),
        as_of=date.today() + timedelta(days=1) if state == "next_day" else date.today(),
    )
    eligibility = peer_set_calculation_eligibility(record, diagnostics=diagnostics)
    assert eligibility["canCalculate"] is False
    assert blocker in eligibility["blockers"]
    if state == "sparse":
        assert eligibility["usableMethods"] == []


def test_eligibility_keeps_valid_legacy_json_evidence_usable(client, db_session):
    from app.services.peer_valuation_sets import peer_set_calculation_eligibility
    target = _company(db_session, "LEGACYELIG")
    created = _create_peer_set(client, target.id)
    reviewed = response_data(client.post(
        f"/api/valuation/relative/peer-sets/{created['id']}/review", json=_review_payload(created),
    ))
    record = db_session.get(PeerValuationSet, reviewed["id"])
    record.member_records.clear()
    assert peer_set_calculation_eligibility(record)["canCalculate"] is True


def _company(db_session, ticker: str) -> Company:
    company = Company(
        ticker=ticker,
        name=f"{ticker} Company",
        market="US",
        primary_exchange="NASDAQ",
        local_symbol=ticker,
        country="United States",
        currency="USD",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def _members(*, count: int = 3, pe_values: list[float] | None = None) -> list[dict]:
    pe_values = pe_values or [10.0, 14.0, 18.0]
    return [
        {
            "identifier": f"PEER{index + 1}",
            "name": f"Peer {index + 1}",
            "included": True,
            "multiples": {
                "pe": pe_values[index],
                "ev_ebitda": 6.0 + index,
            },
            "sourceName": "Reviewed annual filing",
            "sourceUrl": f"https://filings.example.com/peer-{index + 1}",
            "sourceAsOf": "2026-01-31",
            "claimType": "Fact",
        }
        for index in range(count)
    ]


def _target_context(**overrides) -> dict:
    return {
        "sourceName": "Reviewed target filing",
        "sourceUrl": "https://filings.example.com/target",
        "sourceAsOf": "2026-01-31",
        "claimType": "Fact",
        "country": "United States",
        "currency": "USD",
        "fiscalPeriodEnd": "2025-12-31",
        "accountingStandard": "US GAAP",
        "marketCap": 2_000_000,
        "revenueGrowthPct": 10.0,
        "ebitdaMarginPct": 22.0,
        **overrides,
    }


def _create_peer_set(
    client,
    company_id: int,
    *,
    members: list[dict] | None = None,
    target_context: dict | None = None,
) -> dict:
    payload = {
        "companyId": company_id,
        "name": "Reviewed operating peers",
        "notes": "Comparable revenue model and reporting period.",
        "members": members or _members(),
    }
    if target_context is not None:
        payload["targetContext"] = target_context
    response = client.post(
        "/api/valuation/relative/peer-sets",
        json=payload,
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def _review_payload(peer_set: dict, *, acknowledged: bool = True) -> dict:
    return {
        "acknowledged": acknowledged,
        "expectedVersion": peer_set["version"],
        "expectedDiagnosticsSha256": peer_set["diagnostics"]["acknowledgementSha256"],
        "acknowledgedWarningCodes": peer_set["diagnostics"]["warningCodes"],
    }


def test_peer_set_create_calculates_draft_medians_and_provenance(client, db_session) -> None:
    target = _company(db_session, "TARGET")

    peer_set = _create_peer_set(client, target.id)

    assert peer_set["reviewStatus"] == "draft"
    assert peer_set["calculationEligibility"]["canCalculate"] is False
    assert "review_required" in peer_set["calculationEligibility"]["blockers"]
    assert peer_set["version"] == 1
    assert peer_set["aggregationMethod"] == "median"
    assert peer_set["aggregates"]["methods"]["pe"]["multiple"] == 14.0
    assert peer_set["aggregates"]["methods"]["pe"]["eligibleCount"] == 3
    assert peer_set["members"][0]["sourceUrl"].startswith("https://")
    assert peer_set["members"][0]["claimType"] == "Fact"
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert [(item["version"], item["action"]) for item in history] == [(1, "create")]


def test_peer_review_rejects_stale_diagnostic_receipt(client, db_session) -> None:
    target = _company(db_session, "STALEHASH")
    peer_set = _create_peer_set(client, target.id)
    payload = _review_payload(peer_set)
    payload["expectedDiagnosticsSha256"] = "0" * 64

    response = client.post(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
        json=payload,
    )

    assert response.status_code == 409
    assert "diagnostics changed" in response_errors(response)[0]["message"].lower()
    stored = db_session.get(PeerValuationSet, peer_set["id"])
    assert stored.review_status == "draft"
    assert stored.version == 1


def test_peer_review_requires_exact_warning_acknowledgement(client, db_session) -> None:
    target = _company(db_session, "WARNINGACK")
    peer_set = _create_peer_set(client, target.id)
    payload = _review_payload(peer_set)
    payload["acknowledgedWarningCodes"] = []

    response = client.post(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
        json=payload,
    )

    assert response.status_code == 422
    assert "warning codes" in response_errors(response)[0]["message"].lower()


def test_peer_review_receipt_is_versioned_and_update_invalidates_it(client, db_session) -> None:
    target = _company(db_session, "RECEIPT")
    peer_set = _create_peer_set(client, target.id)

    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )

    assert reviewed["reviewReceipt"] == {
        "diagnosticsSha256": peer_set["diagnostics"]["acknowledgementSha256"],
        "warningCodes": peer_set["diagnostics"]["warningCodes"],
        "diagnosticsAsOf": peer_set["diagnostics"]["asOf"],
        "matchesCurrentDiagnostics": True,
    }
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert history[0]["reviewReceipt"] == reviewed["reviewReceipt"]
    assert "reviewReceipt" in history[0]["changedFields"]

    updated = response_data(
        client.put(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}",
            json={"expectedVersion": reviewed["version"], "notes": "Reconsidered evidence."},
        )
    )
    assert updated["reviewStatus"] == "draft"
    assert updated["reviewReceipt"] is None
    updated_history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert "reviewReceipt" in updated_history[0]["changedFields"]


def test_legacy_review_without_receipt_is_blocked_until_reacknowledged(client, db_session) -> None:
    target = _company(db_session, "LEGACYREVIEW")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    stored = db_session.get(PeerValuationSet, peer_set["id"])
    stored.review_diagnostics_sha256 = None
    stored.review_warning_codes_json = None
    stored.review_diagnostics_as_of = None
    db_session.commit()

    blocked = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": peer_set["id"],
            "financials": {"netIncome": 12.0, "dilutedShares": 6.0},
            "methods": ["pe"],
        },
    )
    assert "acknowledgement is missing or stale" in response_errors(blocked)[0]["message"]

    current = response_data(client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}"))
    assert current["reviewStatus"] == "reviewed"
    assert current["reviewReceipt"] is None
    reacknowledged = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(current),
        )
    )
    assert reacknowledged["version"] == reviewed["version"] + 1
    assert reacknowledged["reviewReceipt"]["matchesCurrentDiagnostics"] is True

    allowed = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": peer_set["id"],
            "financials": {"netIncome": 12.0, "dilutedShares": 6.0},
            "methods": ["pe"],
        },
    )
    assert allowed.status_code == 200
    assert response_data(allowed)["benchmarkType"] == "reviewed_peer_set"


def test_corrupt_warning_receipt_is_not_treated_as_current(client, db_session) -> None:
    target = _company(db_session, "CORRUPTRECEIPT")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    stored = db_session.get(PeerValuationSet, reviewed["id"])
    stored.review_warning_codes_json = []
    db_session.commit()

    current = response_data(client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}"))
    assert current["reviewReceipt"]["matchesCurrentDiagnostics"] is False
    blocked = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": peer_set["id"],
            "financials": {"netIncome": 12.0, "dilutedShares": 6.0},
            "methods": ["pe"],
        },
    )
    assert "acknowledgement is missing or stale" in response_errors(blocked)[0]["message"]

    reacknowledged = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(current),
        )
    )
    assert reacknowledged["reviewReceipt"]["matchesCurrentDiagnostics"] is True


def test_target_context_is_normalized_and_snapshotted(client, db_session) -> None:
    target = _company(db_session, "TARGETCTX")
    peer_set = _create_peer_set(
        client,
        target.id,
        target_context=_target_context(currency="usd"),
    )

    assert peer_set["targetContext"]["currency"] == "USD"
    assert peer_set["targetStorageConsistency"]["status"] == "consistent"
    current_profile = db_session.query(PeerValuationTargetProfile).one()
    revision_profile = db_session.query(PeerValuationRevisionTargetProfile).one()
    assert current_profile.peer_set_id == peer_set["id"]
    assert current_profile.market_cap == 2_000_000
    assert revision_profile.currency == "USD"
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert history[0]["targetContext"]["sourceName"] == "Reviewed target filing"
    assert history[0]["targetStorageConsistency"]["status"] == "consistent"


def test_target_context_update_invalidates_review_and_versions_snapshot(client, db_session) -> None:
    target = _company(db_session, "TARGETUPDATE")
    peer_set = _create_peer_set(client, target.id, target_context=_target_context())
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )

    updated = response_data(
        client.put(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}",
            json={
                "expectedVersion": reviewed["version"],
                "targetContext": _target_context(revenueGrowthPct=35.0),
            },
        )
    )

    assert updated["reviewStatus"] == "draft"
    assert updated["version"] == 3
    assert updated["targetContext"]["revenueGrowthPct"] == 35.0
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert history[0]["changedFields"] == ["targetContext", "reviewStatus", "reviewReceipt"]
    assert history[1]["targetContext"]["revenueGrowthPct"] == 10.0


def test_target_relative_diagnostics_propagate_to_valuation(client, db_session) -> None:
    target = _company(db_session, "TARGETDIAG")
    members = _members()
    members[0].update(
        {
            "country": "Canada",
            "currency": "CAD",
            "fiscalPeriodEnd": "2024-06-30",
            "accountingStandard": "IFRS",
            "marketCap": 30_000_000,
            "revenueGrowthPct": 40.0,
            "ebitdaMarginPct": 50.0,
        }
    )
    for member in members[1:]:
        member.update(
            {
                "country": "United States",
                "currency": "USD",
                "fiscalPeriodEnd": "2025-12-31",
                "accountingStandard": "US GAAP",
                "marketCap": 2_000_000,
                "revenueGrowthPct": 10.0,
                "ebitdaMarginPct": 22.0,
            }
        )
    peer_set = _create_peer_set(
        client,
        target.id,
        members=members,
        target_context=_target_context(),
    )
    codes = {warning["code"] for warning in peer_set["diagnostics"]["warnings"]}
    assert {
        "target_currency_mismatch",
        "target_country_mismatch",
        "target_accounting_mismatch",
        "target_fiscal_period_mismatch",
        "target_growth_mismatch",
        "target_margin_mismatch",
    }.issubset(codes)
    assert peer_set["diagnostics"]["comparabilityContext"]["targetProvided"] is True
    assert (
        peer_set["diagnostics"]["comparabilityContext"]["targetComparisons"]["marketCap"]
        ["mismatchCount"]
        == 0
    )
    assert (
        peer_set["diagnostics"]["comparabilityContext"]["targetComparisons"]["marketCap"]
        ["comparedCount"]
        == 2
    )
    assert (
        peer_set["diagnostics"]["comparabilityContext"]["targetComparisons"]["marketCap"]
        ["skippedCurrencyMismatchCount"]
        == 1
    )

    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    result = response_data(
        client.post(
            "/api/valuation/relative/run",
            json={
                "companyId": str(target.id),
                "peerSetId": reviewed["id"],
                "financials": {"netIncome": 12.0, "dilutedShares": 6.0},
                "methods": ["pe"],
            },
        )
    )
    assert result["relativeValues"][0]["reliability"] == "low"
    assert result["relativeValues"][0]["source"]["targetContext"]["currency"] == "USD"


def test_target_storage_mismatch_blocks_reviewed_valuation(client, db_session) -> None:
    target = _company(db_session, "TARGETSTORE")
    peer_set = _create_peer_set(client, target.id, target_context=_target_context())
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    stored = db_session.get(PeerValuationSet, reviewed["id"])
    stored.target_context_json = {**stored.target_context_json, "revenueGrowthPct": 999.0}
    db_session.commit()

    response = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": reviewed["id"],
            "financials": {"netIncome": 10.0, "dilutedShares": 10.0},
            "methods": ["pe"],
        },
    )
    assert response.status_code == 200
    assert "Target profile storage mismatch" in response_errors(response)[0]["message"]


def test_target_context_requires_real_source_and_comparability_fact(client, db_session) -> None:
    target = _company(db_session, "TARGETVALIDATE")
    no_fact = _target_context()
    for key in (
        "country",
        "currency",
        "fiscalPeriodEnd",
        "accountingStandard",
        "marketCap",
        "revenueGrowthPct",
        "ebitdaMarginPct",
    ):
        no_fact.pop(key)
    no_fact_response = client.post(
        "/api/valuation/relative/peer-sets",
        json={
            "companyId": target.id,
            "name": "No target fact",
            "members": _members(),
            "targetContext": no_fact,
        },
    )
    assert no_fact_response.status_code == 422
    assert "at least one comparability fact" in no_fact_response.text

    mock_response = client.post(
        "/api/valuation/relative/peer-sets",
        json={
            "companyId": target.id,
            "name": "Mock target",
            "members": _members(),
            "targetContext": _target_context(sourceName="Mock Data target"),
        },
    )
    assert mock_response.status_code == 422
    assert "Mock Data" in mock_response.text


def test_peer_set_review_requires_three_eligible_peers(client, db_session) -> None:
    target = _company(db_session, "SMALL")
    peer_set = _create_peer_set(client, target.id, members=_members(count=2, pe_values=[10.0, 12.0]))

    response = client.post(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
        json=_review_payload(peer_set),
    )

    assert response.status_code == 422
    assert "At least 3 included peers" in response_errors(response)[0]["message"]


def test_reviewed_peer_set_drives_relative_valuation_with_member_sources(client, db_session) -> None:
    target = _company(db_session, "VALUE")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    assert reviewed["reviewStatus"] == "reviewed"
    assert reviewed["calculationEligibility"]["canCalculate"] is True
    assert reviewed["calculationEligibility"]["usableMethods"] == ["pe", "ev_ebitda"]

    response = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": peer_set["id"],
            "financials": {
                "netIncome": 20.0,
                "ebitda": 40.0,
                "debt": 10.0,
                "cash": 5.0,
                "dilutedShares": 10.0,
            },
            "methods": ["pe", "ev_ebitda", "pbv"],
        },
    )

    assert response.status_code == 200, response.text
    result = response_data(response)
    assert result["benchmarkType"] == "reviewed_peer_set"
    assert result["peerSet"]["id"] == peer_set["id"]
    values = {item["methodId"]: item for item in result["relativeValues"]}
    assert values["pe"]["benchmarkMultiple"] == 14.0
    assert values["pe"]["valuePerShare"] == 28.0
    assert values["pe"]["source"]["eligibleCount"] == 3
    assert len(values["pe"]["source"]["memberSources"]) == 3
    assert result["unavailableMethods"] == [
        {
            "method": "pbv",
            "reason": "Reviewed peer set has 0 eligible value(s); at least 3 are required",
        }
    ]


def test_draft_peer_set_cannot_drive_relative_valuation(client, db_session) -> None:
    target = _company(db_session, "DRAFT")
    peer_set = _create_peer_set(client, target.id)

    response = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": peer_set["id"],
            "financials": {"netIncome": 10.0, "dilutedShares": 10.0},
            "methods": ["pe"],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] is None
    assert response_errors(response)[0]["code"] == "VALUATION_ERROR"
    assert "must be reviewed" in response_errors(response)[0]["message"]


def test_peer_storage_mismatch_blocks_reviewed_valuation(client, db_session) -> None:
    target = _company(db_session, "MISMATCH")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    stored = db_session.get(PeerValuationSet, reviewed["id"])
    changed_members = list(stored.peer_identifiers_json)
    changed_members[0] = {
        **changed_members[0],
        "multiples": {**changed_members[0]["multiples"], "pe": 999.0},
    }
    stored.peer_identifiers_json = changed_members
    db_session.commit()

    response = client.post(
        "/api/valuation/relative/run",
        json={
            "companyId": str(target.id),
            "peerSetId": reviewed["id"],
            "financials": {"netIncome": 10.0, "dilutedShares": 10.0},
            "methods": ["pe"],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] is None
    assert "storage mismatch" in response_errors(response)[0]["message"]


def test_peer_set_update_invalidates_review_atomically(client, db_session) -> None:
    target = _company(db_session, "UPDATE")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(client.post(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
        json=_review_payload(peer_set),
    ))

    response = client.put(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}",
        json={
            "expectedVersion": reviewed["version"],
            "name": "Updated reviewed peers",
            "members": _members(pe_values=[11.0, 15.0, 19.0]),
        },
    )

    assert response.status_code == 200
    updated = response_data(response)
    assert updated["name"] == "Updated reviewed peers"
    assert updated["reviewStatus"] == "draft"
    assert updated["reviewedAt"] is None
    assert updated["aggregates"]["methods"]["pe"]["multiple"] == 15.0
    assert updated["version"] == 3

    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert [(item["version"], item["action"]) for item in history] == [
        (3, "update"),
        (2, "review"),
        (1, "create"),
    ]
    assert history[0]["changedFields"] == ["name", "members", "reviewStatus", "reviewReceipt"]


def test_peer_set_mutations_reject_stale_versions(client, db_session) -> None:
    target = _company(db_session, "VERSION")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )

    stale_update = client.put(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}",
        json={"expectedVersion": peer_set["version"], "name": "Stale write"},
    )
    assert stale_update.status_code == 409
    assert "reload before saving" in response_errors(stale_update)[0]["message"]

    stale_archive = client.delete(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}"
        f"?expected_version={peer_set['version']}"
    )
    assert stale_archive.status_code == 409
    assert reviewed["version"] == 2


def test_archive_restore_requires_review_and_preserves_history(client, db_session) -> None:
    target = _company(db_session, "RESTORE")
    peer_set = _create_peer_set(client, target.id)
    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    archived = response_data(
        client.delete(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}"
            f"?expected_version={reviewed['version']}"
        )
    )
    restored = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/restore",
            json={"expectedVersion": archived["version"]},
        )
    )

    assert restored["isActive"] is True
    assert restored["reviewStatus"] == "draft"
    assert restored["reviewedAt"] is None
    assert restored["version"] == 4
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{peer_set['id']}/revisions")
    )
    assert [item["action"] for item in history] == ["restore", "archive", "review", "create"]


def test_peer_set_comparability_diagnostics_are_visible_and_propagated(client, db_session) -> None:
    target = _company(db_session, "DIAGNOSTIC")
    members = _members(pe_values=[2.0, 4.0, 12.0])
    members[0]["sourceAsOf"] = (date.today() - timedelta(days=180)).isoformat()
    members[1]["sourceAsOf"] = (date.today() - timedelta(days=60)).isoformat()
    members[2]["sourceAsOf"] = date.today().isoformat()
    members[2]["claimType"] = "Source Summary"
    peer_set = _create_peer_set(client, target.id, members=members)

    warning_codes = {warning["code"] for warning in peer_set["diagnostics"]["warnings"]}
    assert {
        "stale_peer_sources",
        "unaligned_source_dates",
        "source_summary_members",
        "wide_multiple_dispersion",
    }.issubset(warning_codes)
    assert peer_set["diagnostics"]["methods"]["pe"]["maxToMinRatio"] == 6.0

    reviewed = response_data(
        client.post(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
            json=_review_payload(peer_set),
        )
    )
    result = response_data(
        client.post(
            "/api/valuation/relative/run",
            json={
                "companyId": str(target.id),
                "peerSetId": reviewed["id"],
                "financials": {"netIncome": 12.0, "dilutedShares": 6.0},
                "methods": ["pe"],
            },
        )
    )
    assert result["relativeValues"][0]["reliability"] == "low"
    assert result["relativeValues"][0]["source"]["warnings"]
    assert any("widely dispersed" in item for item in result["diagnostics"])


def test_peer_members_and_revision_members_are_normalized(client, db_session) -> None:
    target = _company(db_session, "NORMALIZED")
    members = _members()
    for index, member in enumerate(members):
        member.update(
            {
                "country": "United States",
                "currency": "usd",
                "fiscalPeriodEnd": "2025-12-31",
                "accountingStandard": "US GAAP",
                "marketCap": 1_000_000 + index * 100_000,
                "revenueGrowthPct": 8.0 + index,
                "ebitdaMarginPct": 20.0 + index,
            }
        )
    peer_set = _create_peer_set(client, target.id, members=members)

    current_rows = (
        db_session.query(PeerValuationMemberRecord)
        .filter(PeerValuationMemberRecord.peer_set_id == peer_set["id"])
        .order_by(PeerValuationMemberRecord.ordinal)
        .all()
    )
    revision_rows = db_session.query(PeerValuationRevisionMemberRecord).all()
    assert len(current_rows) == 3
    assert len(revision_rows) == 3
    assert current_rows[0].currency == "USD"
    assert current_rows[0].accounting_standard == "US GAAP"
    assert current_rows[0].market_cap == 1_000_000
    assert peer_set["storageConsistency"]["status"] == "consistent"


def test_comparability_context_warns_without_creating_a_fake_score(client, db_session) -> None:
    target = _company(db_session, "CONTEXT")
    members = _members()
    contexts = [
        ("USD", "US GAAP", "2025-12-31", 1_000_000, 5.0, 10.0),
        ("EUR", "IFRS", "2025-06-30", 12_000_000, 30.0, 30.0),
        ("USD", "US GAAP", "2025-12-31", 2_000_000, 8.0, 12.0),
    ]
    for member, context in zip(members, contexts, strict=True):
        currency, standard, period, market_cap, growth, margin = context
        member.update(
            {
                "currency": currency,
                "accountingStandard": standard,
                "fiscalPeriodEnd": period,
                "marketCap": market_cap,
                "revenueGrowthPct": growth,
                "ebitdaMarginPct": margin,
            }
        )
    peer_set = _create_peer_set(client, target.id, members=members)

    codes = {warning["code"] for warning in peer_set["diagnostics"]["warnings"]}
    assert {
        "mixed_peer_currencies",
        "mixed_accounting_standards",
        "unaligned_fiscal_periods",
        "wide_growth_dispersion",
        "wide_margin_dispersion",
    }.issubset(codes)
    assert "wide_size_dispersion" not in codes
    assert peer_set["diagnostics"]["comparabilityContext"]["marketCapRatio"] is None
    assert "score" not in peer_set["diagnostics"]


def _peer_csv(
    client,
    *,
    set_name: str = "Imported peers",
    target_context: dict | None = None,
) -> tuple[str, list[str]]:
    template = response_data(client.get("/api/valuation/relative/peer-sets/import/template"))
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=template["columns"])
    writer.writeheader()
    for index in range(3):
        row = {
                "set_name": set_name,
                "set_notes": "Source-preserving import",
                "identifier": f"CSV{index + 1}",
                "name": f"CSV Peer {index + 1}",
                "included": "true",
                "source_name": "Reviewed filing",
                "source_url": f"https://filings.example.com/csv-{index + 1}",
                "source_as_of": date.today().isoformat(),
                "claim_type": "Fact",
                "country": "United States",
                "currency": "USD",
                "fiscal_period_end": (date.today() - timedelta(days=30)).isoformat(),
                "accounting_standard": "US GAAP",
                "market_cap": 1_000_000 + index * 100_000,
                "revenue_growth_pct": 8 + index,
                "ebitda_margin_pct": 20 + index,
                "pe": 10 + index * 2,
                "ev_ebitda": 6 + index,
            }
        if target_context:
            row.update(
                {
                    "target_source_name": target_context.get("sourceName", ""),
                    "target_source_url": target_context.get("sourceUrl", ""),
                    "target_source_as_of": target_context.get("sourceAsOf", ""),
                    "target_claim_type": target_context.get("claimType", ""),
                    "target_notes": target_context.get("notes", ""),
                    "target_country": target_context.get("country", ""),
                    "target_currency": target_context.get("currency", ""),
                    "target_fiscal_period_end": target_context.get("fiscalPeriodEnd", ""),
                    "target_accounting_standard": target_context.get("accountingStandard", ""),
                    "target_market_cap": target_context.get("marketCap", ""),
                    "target_revenue_growth_pct": target_context.get("revenueGrowthPct", ""),
                    "target_ebitda_margin_pct": target_context.get("ebitdaMarginPct", ""),
                }
            )
        writer.writerow(row)
    return stream.getvalue(), template["columns"]


def test_peer_csv_preview_apply_export_and_formula_safety(client, db_session) -> None:
    target = _company(db_session, "CSV")
    csv_text, columns = _peer_csv(client, set_name="=Imported peers")
    preview = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": csv_text},
        )
    )
    assert preview["isValid"] is True
    assert preview["memberCount"] == 3
    assert preview["errors"] == []
    assert len(preview["sha256"]) == 64

    applied = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/apply",
            json={
                "companyId": target.id,
                "csvText": csv_text,
                "expectedSha256": preview["sha256"],
            },
        )
    )
    assert applied["reviewStatus"] == "draft"
    assert applied["name"] == "=Imported peers"
    history = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{applied['id']}/revisions")
    )
    assert history[0]["action"] == "import"

    exported = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{applied['id']}/export")
    )
    assert exported["rowCount"] == 3
    assert exported["csvText"].splitlines()[0].split(",") == columns
    assert "'=Imported peers" in exported["csvText"]
    roundtrip = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": exported["csvText"]},
        )
    )
    assert roundtrip["isValid"] is True
    assert roundtrip["setName"] == "=Imported peers"


def test_peer_csv_roundtrips_sourced_target_profile(client, db_session) -> None:
    target = _company(db_session, "CSVTARGET")
    target_context = _target_context(sourceName="=Reviewed target filing", notes="+Target note")
    csv_text, columns = _peer_csv(client, target_context=target_context)

    preview = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": csv_text},
        )
    )
    assert preview["isValid"] is True
    assert preview["formatVersion"] == "2"
    assert preview["legacyFormat"] is False
    assert preview["targetContext"]["sourceName"] == "=Reviewed target filing"
    assert preview["targetContext"]["currency"] == "USD"

    applied = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/apply",
            json={
                "companyId": target.id,
                "csvText": csv_text,
                "expectedSha256": preview["sha256"],
            },
        )
    )
    assert applied["reviewStatus"] == "draft"
    assert applied["targetContext"]["marketCap"] == 2_000_000
    assert applied["targetStorageConsistency"]["status"] == "consistent"

    exported = response_data(
        client.get(f"/api/valuation/relative/peer-sets/{applied['id']}/export")
    )
    assert exported["formatVersion"] == "2"
    assert exported["targetContextIncluded"] is True
    assert exported["csvText"].splitlines()[0].split(",") == columns
    assert "'=Reviewed target filing" in exported["csvText"]
    assert "'+Target note" in exported["csvText"]

    roundtrip = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": exported["csvText"]},
        )
    )
    assert roundtrip["isValid"] is True
    assert roundtrip["targetContext"] == preview["targetContext"]


def test_peer_csv_rejects_inconsistent_or_invalid_target_profile(client, db_session) -> None:
    target = _company(db_session, "CSVTARGETERR")
    csv_text, columns = _peer_csv(client, target_context=_target_context())
    rows = list(csv.DictReader(StringIO(csv_text)))
    rows[1]["target_currency"] = "CAD"
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

    inconsistent = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": stream.getvalue()},
        )
    )
    assert inconsistent["isValid"] is False
    assert any(error["field"] == "target_context" for error in inconsistent["errors"])

    invalid_text, invalid_columns = _peer_csv(
        client,
        target_context=_target_context(sourceName="Mock Data target"),
    )
    invalid = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": invalid_text},
        )
    )
    assert invalid_columns == columns
    assert invalid["isValid"] is False
    assert any(error["field"].startswith("targetContext") for error in invalid["errors"])


def test_peer_csv_accepts_legacy_member_only_header_with_visible_warning(client, db_session) -> None:
    target = _company(db_session, "CSVLEGACY")
    csv_text, columns = _peer_csv(client)
    target_columns = [column for column in columns if column.startswith("target_")]
    rows = list(csv.DictReader(StringIO(csv_text)))
    legacy_columns = [column for column in columns if column not in target_columns]
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=legacy_columns)
    writer.writeheader()
    writer.writerows(
        [{key: value for key, value in row.items() if key in legacy_columns} for row in rows]
    )

    preview = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": stream.getvalue()},
        )
    )
    assert preview["isValid"] is True
    assert preview["legacyFormat"] is True
    assert preview["targetContext"] is None
    assert any("Legacy peer-only CSV" in warning for warning in preview["warnings"])


def test_peer_csv_rejects_header_errors_rows_and_changed_apply(client, db_session) -> None:
    target = _company(db_session, "CSVERR")
    invalid = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": "wrong,header\n1,2\n"},
        )
    )
    assert invalid["isValid"] is False
    assert invalid["errors"][0]["field"] == "header"

    csv_text, _ = _peer_csv(client)
    preview = response_data(
        client.post(
            "/api/valuation/relative/peer-sets/import/preview",
            json={"companyId": target.id, "csvText": csv_text},
        )
    )
    changed = client.post(
        "/api/valuation/relative/peer-sets/import/apply",
        json={
            "companyId": target.id,
            "csvText": csv_text + "\n",
            "expectedSha256": preview["sha256"],
        },
    )
    assert changed.status_code == 409
    assert "changed after preview" in response_errors(changed)[0]["message"]


def test_peer_set_rejects_duplicate_self_and_mock_members(client, db_session) -> None:
    target = _company(db_session, "GUARD")
    duplicate_members = _members()
    duplicate_members[1]["identifier"] = duplicate_members[0]["identifier"]
    duplicate = client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": target.id, "name": "Duplicates", "members": duplicate_members},
    )
    assert duplicate.status_code == 422
    assert "Duplicate peer identifier" in response_errors(duplicate)[0]["message"]

    self_members = _members()
    self_members[0]["companyId"] = target.id
    self_member = client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": target.id, "name": "Self", "members": self_members},
    )
    assert self_member.status_code == 422
    assert "cannot be its own peer" in response_errors(self_member)[0]["message"]

    mock_members = _members()
    mock_members[0]["sourceName"] = "Mock Data fixture"
    mock = client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": target.id, "name": "Mock", "members": mock_members},
    )
    assert mock.status_code == 422
    assert "Mock Data" in response_errors(mock)[0]["message"]


def test_peer_sets_are_owner_scoped_and_archive_is_recoverable(client, db_session) -> None:
    target = _company(db_session, "OWNED")
    peer_set = _create_peer_set(client, target.id)
    other = User(id="other-peer-user", email="other-peer@example.com", name="Other")
    db_session.add(other)
    db_session.add(
        PeerValuationSet(
            company_id=target.id,
            user_id=other.id,
            name="Other user's peers",
            peer_identifiers_json=[],
            aggregate_metrics_json={},
        )
    )
    db_session.commit()

    listed = response_data(
        client.get(f"/api/valuation/relative/peer-sets?company_id={target.id}")
    )
    assert [item["id"] for item in listed] == [peer_set["id"]]

    archived = response_data(
        client.delete(
            f"/api/valuation/relative/peer-sets/{peer_set['id']}"
            f"?expected_version={peer_set['version']}"
        )
    )
    assert archived["isActive"] is False
    assert response_data(
        client.get(f"/api/valuation/relative/peer-sets?company_id={target.id}")
    ) == []
    archived_list = response_data(
        client.get(
            f"/api/valuation/relative/peer-sets?company_id={target.id}&include_archived=true"
        )
    )
    assert [item["id"] for item in archived_list] == [peer_set["id"]]


def test_peer_set_rejects_future_source_date_and_non_positive_multiple(client, db_session) -> None:
    target = _company(db_session, "DATES")
    future = _members()
    future[0]["sourceAsOf"] = "2099-01-01"
    future_response = client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": target.id, "name": "Future", "members": future},
    )
    assert future_response.status_code == 422
    assert "cannot be in the future" in response_errors(future_response)[0]["message"]

    zero = _members()
    zero[0]["multiples"]["pe"] = 0
    zero_response = client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": target.id, "name": "Zero", "members": zero},
    )
    assert zero_response.status_code == 422


def test_missing_country_stats_returns_country_metadata(client) -> None:
    response = client.get("/api/valuation/relative/countries/NO-SUCH-COUNTRY/stats")

    assert response.status_code == 200
    assert response.json()["data"] is None
    assert response.json()["meta"]["source"] == "Damodaran country statistics"
    assert response_errors(response)[0]["code"] == "NOT_FOUND"


def test_peer_set_routes_are_authenticated_and_use_api_envelopes() -> None:
    expected_paths = {
        "/api/valuation/relative/peer-sets",
        "/api/valuation/relative/peer-sets/{peer_set_id}",
        "/api/valuation/relative/peer-sets/{peer_set_id}/review",
        "/api/valuation/relative/peer-sets/{peer_set_id}/restore",
        "/api/valuation/relative/peer-sets/{peer_set_id}/revisions",
        "/api/valuation/relative/peer-sets/{peer_set_id}/export",
        "/api/valuation/relative/peer-sets/import/template",
        "/api/valuation/relative/peer-sets/import/preview",
        "/api/valuation/relative/peer-sets/import/apply",
    }
    security = [
        item
        for item in build_route_security_inventory(app)
        if item.path in expected_paths
    ]
    contracts = [
        item
        for item in build_response_contract_inventory(app)
        if item.path in expected_paths
    ]

    assert security
    assert {item.path for item in security} == expected_paths
    assert all(item.classification == "authenticated" for item in security)
    assert all(item.has_auth_dependency for item in security)
    assert contracts
    assert {item.path for item in contracts} == expected_paths
    assert all(item.contract == "api_envelope" for item in contracts)
