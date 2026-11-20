from datetime import UTC, date, datetime
from uuid import uuid4

from app.models.dcf import DcfAssumptionSet, DcfDecisionLog, DcfOutput, DcfProjectionYear, DcfSensitivityTable, ValuationModel
from test_dated_financial_inputs import setup
from test_valuation_setup_drafts import _valid_review_value


def fact(db, company, source, value, published, suffix, **locator):
    from app.models import FinancialExtractionCandidate, RawDocument
    from app.services.source_fact_history import record_financial_fact_revision
    document = RawDocument(company_id=company.id,source_id=source.id,document_type="annual_report",
        title="Mock Data annual report",content_hash="release-fixture-"+suffix,published_at=published)
    db.add(document); db.flush()
    candidate=FinancialExtractionCandidate(company_id=company.id,raw_document_id=document.id,
        metric_code=locator.pop("metric","revenue"),reported_label="Mock Data consolidated total",
        value=value,unit="USD million",fiscal_year=2026,period_type="annual",review_status="promoted",
        extraction_method="mock",source_text="Mock Data original",source_locator_json={
            "start":"2025-10-01","end":"2026-09-30","claim_type":"Mock Data",**locator})
    db.add(candidate); db.flush()
    revision=record_financial_fact_revision(db,candidate,effective_at=date(2026,9,30))
    db.flush()
    return revision


def prepared(client, db):
    company, source = setup(db)
    revision = fact(db, company, source, 100, datetime(2026, 11, 1, tzinfo=UTC), "v",
        accounting_basis="us-gaap", consolidation_scope="consolidated")
    db.commit()
    draft = client.post(f"/companies/{company.id}/valuation-drafts", json={}).json()["data"]
    base = f"/valuation-drafts/{draft['id']}"
    fields = draft["source_metadata_json"]["review_fields_by_model"]["fcff_dcf"]
    values = {k: _valid_review_value(k) for k in fields}
    values.update(starting_revenue=None, starting_invested_capital=50_000_000,
        revenue_growth_years_json={str(i): 0 for i in range(1, 11)}, projection_years_count=10,
        target_operating_margin=.2, current_operating_margin=.2, tax_rate=.25, sales_to_capital_ratio=2,
        wacc_start=.10, wacc_terminal=.10, terminal_growth_rate=0, terminal_roic=.10,
        cash=5_000_000, debt=20_000_000, diluted_shares=10_000_000, current_market_price=None,
        cross_holdings=0, operating_leases=0, minority_interests=0, preferred_stock=0,
        employee_options_value=0, cash_flow_currency="USD", discount_rate_currency="USD")
    from app.services.assumption_provenance import DISCOUNT_COMPONENT_FIELDS
    values.update({k: None for k in DISCOUNT_COMPONENT_FIELDS})
    draft = client.patch(base, json={"assumptions_patch": values, "reviewed_fields": list(values)}).json()["data"]
    selection = dict(kind="source_fact_revision", id=revision.id, target_field="starting_revenue")
    command = dict(expected_updated_at=draft["updated_at"], valuation_date="2026-11-12", selections=[selection])
    attached = client.put(base+"/source-proposal", json=command)
    assert attached.status_code == 200, attached.text
    command = dict(expected_updated_at=attached.json()["data"]["updated_at"], valuation_date="2026-11-12", name="Mock Data first valuation")
    return base, command, company, source, selection


def counts(db):
    return [db.query(m).count() for m in (ValuationModel, DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable, DcfDecisionLog)]


def test_first_preview_and_durable_confirmation(client, db):
    base, cmd, company, source, ref = prepared(client, db)
    assert client.post(base+"/promote", json={"name":"Skip preview"}).status_code == 409
    preview = client.post(base+"/preview", json=cmd).json()["data"]
    assert preview["ready"], preview["blockers"]
    assert counts(db) == [0]*6
    assert preview["assumptions"]["starting_revenue"] == 100_000_000
    assert preview["sources"][0]["ref"] == ref
    assert preview["sources"][0]["source"]["claim_type"] == "Mock Data"
    assert abs(preview["proposed_output"]["intrinsic_value_per_share"] - 13.50) < 1e-9
    assert abs(preview["proposed_output"]["enterprise_value"] - 150_000_000) < .01
    frozen = dict(**cmd, preview_hash=preview["preview_hash"], submission_id=str(uuid4()), reason="Reviewed the original annual filing")
    saved = client.post(base+"/confirm", json=frozen)
    assert saved.status_code == 201, saved.text
    assert counts(db) == [1,1,1,10,6,1]
    fact(db, company, source, 101, datetime(2026,11,2,tzinfo=UTC), "replaced", accounting_basis="us-gaap", consolidation_scope="consolidated")
    db.commit()
    db.expire_all()
    retry = client.post(base+"/confirm", json=frozen)
    assert retry.status_code == 200 and retry.json()["data"]["replayed"]
    assert retry.json()["data"]["assumption_set_id"] == saved.json()["data"]["assumption_set_id"]
    assert client.post(base+"/confirm", json={**frozen, "reason":"different"}).status_code == 409
    assert counts(db) == [1,1,1,10,6,1]


def test_revision_changed_or_borrowings_incomplete_hold_first_save(client, db):
    base, cmd, company, source, ref = prepared(client, db)
    preview = client.post(base+"/preview", json=cmd).json()["data"]
    fact(db, company, source, 100, datetime(2026,11,2,tzinfo=UTC), "same-value-revision", accounting_basis="us-gaap", consolidation_scope="consolidated")
    db.commit()
    changed = client.post(base+"/preview", json=cmd).json()["data"]
    assert not changed["ready"] and changed["proposed_output"] is None
    frozen = dict(**cmd, preview_hash=preview["preview_hash"], submission_id=str(uuid4()), reason="Reviewed Mock Data")
    assert client.post(base+"/confirm", json=frozen).status_code == 409
    candidate = fact(db, company, source, 21, datetime(2026,11,3,tzinfo=UTC), "borrowing", accounting_basis="us-gaap",metric="debt")
    db.commit()
    sel = {"kind":"source_fact_revision", "id":candidate.id, "target_field":"debt"}
    draft = client.put(base+"/source-proposal", json={"expected_updated_at":cmd["expected_updated_at"],
        "valuation_date":cmd["valuation_date"],"selections":[sel]}).json()["data"]
    held = client.post(base+"/preview", json={**cmd, "expected_updated_at":draft["updated_at"]}).json()["data"]
    assert not held["ready"] and held["proposed_output"] is None
    assert any("debt" in x.lower() for x in held["blockers"])
    assert counts(db) == [0]*6


def test_foreign_owner_cannot_preview_confirm_or_recover_first_version(client, db):
    from app.api.dependencies import get_current_user
    from app.main import app
    from app.models import User
    base, cmd, *_ = prepared(client, db)
    preview=client.post(base+"/preview",json=cmd).json()["data"]
    frozen={**cmd,"preview_hash":preview["preview_hash"],"submission_id":str(uuid4()),"reason":"Mock Data reason"}
    assert client.post(base+"/confirm",json=frozen).status_code==201
    db.add(User(id="other-first-owner",name="Second Mock Data owner",email="other-first@example.invalid"))
    db.commit()
    app.dependency_overrides[get_current_user]=lambda:{"id":"other-first-owner"}
    assert client.post(base+"/preview",json=cmd).status_code==404
    assert client.post(base+"/confirm",json=frozen).status_code==404
    assert client.put(base+"/source-proposal",json={"expected_updated_at":cmd["expected_updated_at"],
        "valuation_date":cmd["valuation_date"],"selections":[]}).status_code==404


def test_benchmark_eligibility_requires_both_source_publications(client, db):
    from types import SimpleNamespace
    from app.models import DamodaranDatasetFile, RawDocument, Source
    from app.services.draft_source_proposal import dated_prior_blockers
    from test_weighted_industry_mix import _company_and_benchmarks, _payload
    company=_company_and_benchmarks(db)
    dataset=db.query(DamodaranDatasetFile).one()
    dataset.source_sha256="a"*64
    db.add(source:=Source(name="Mock Data annual source",source_type="filing"))
    db.flush()
    db.add(document:=RawDocument(company_id=company.id,source_id=source.id,document_type="annual_report",
        title="Mock Data segment table",content_hash="segment-hash",published_at=datetime(2026,11,14,tzinfo=UTC)))
    db.commit()
    mix=client.put(f"/companies/{company.id}/industry-allocations",json={**_payload(),"as_of_date":"2026-09-30","source_document_id":document.id})
    assert mix.status_code==200,mix.text
    provenance={"source_type":"industry_benchmark_blend","source_summary":[{"sources":[{"dataset_file_id":dataset.id}]}]}
    draft=SimpleNamespace(provenance_json={"target_operating_margin":provenance})
    day=date(2026,11,12)
    def problems():
        return dated_prior_blockers(db,draft,company.id,day,{"target_operating_margin"})
    assert len(problems())==2
    url=f"/api/admin/damodaran/datasets/{dataset.id}/publication"
    record={"source_sha256":dataset.source_sha256,"publication_date":"2026-01-09","publication_source":"https://example.invalid/mock-release"}
    assert client.put(url,json=record).status_code==200
    assert client.put(url,json={**record,"publication_date":"2025-01-09"}).status_code==409
    assert len(problems())==1 and "weights" in problems()[0]
    document.published_at=datetime(2026,11,10,tzinfo=UTC); db.commit()
    assert problems()==[]
    dataset.publication_date=date(2026,11,13); db.commit()
    assert len(problems())==1 and "benchmark publication" in problems()[0]
