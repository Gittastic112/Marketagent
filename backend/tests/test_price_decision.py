from datetime import UTC, datetime
from uuid import uuid4

from app.models import DcfAssumptionSet, RawDocument, Source, ThesisNote, User, ValuationModel
from app.models.thesis_note import ThesisAssumption, ThesisChange
from app.api.dependencies import get_current_user
from app.main import app
from conftest import TEST_USER_ID
from test_company_price_timeline import close, company


def test_chart_decision_keeps_historical_anchor_ownership_and_exact_evidence(db, client):
    issuer = company(db,"CHARTDEC")
    other = User(id="other-reviewer", email="mock-owner2@example.invalid", name="Mock owner two")
    db.add(other)
    notes = [ThesisNote(user_id=owner, company_id=issuer.id, title="Mock thesis", thesis_text="Mock Data")
             for owner in (TEST_USER_ID,other.id)]
    db.add_all(notes); db.flush()
    assumptions = [ThesisAssumption(thesis_note_id=n.id,description="Reviewed margin") for n in notes]
    db.add_all(assumptions)
    db.add(source := Source(name="Mock original",source_type="filing")); db.flush()
    doc = RawDocument(company_id=issuer.id,source_id=source.id,title="Mock filing",document_type="annual_report",
        content_hash="decision-fixture",published_at=datetime(2026,1,6,22,tzinfo=UTC),raw_text="Mock Data original")
    db.add(doc)
    p = close(db,issuer,"2026-01-06","90",source_timestamp=datetime(2026,1,6,21,tzinfo=UTC))
    db.commit()
    point = client.get(f"/companies/{issuer.id}/price-timeline").json()["data"]["points"][0]
    pin = client.post(f"/companies/{issuer.id}/price-timeline/pins", json={"thesis_id":notes[0].id,"price_id":p.id,
        "fingerprint":point["fingerprint"],"request_id":str(uuid4()),"text":"Mock Data check"}).json()["data"]
    root = f"/thesis-notes/{notes[0].id}/price-pins/{pin['id']}"
    body = {"assumption_id":assumptions[0].id,"original":{"kind":"raw_document","id":doc.id},
            "decision":"no_change","reason":"The release followed the close."}
    assert client.get(root+"/decision-options").json()["data"]["originals"][0]["document_id"] == doc.id
    preview = client.post(root+"/decision-preview",json=body).json()["data"]
    assert preview["context"]["original"]["temporal_scope"] == "after_close"
    frozen = {**body,"context_hash":preview["context_hash"],"request_id":str(uuid4())}
    p.price=93
    db.commit()
    assert client.post(root+"/decision-preview",json={**body,"assumption_id":assumptions[1].id}).status_code == 404
    result = client.post(root+"/decisions",json=frozen)
    assert result.status_code == 201, result.text
    stored=db.get(ThesisChange,result.json()["data"]["change_id"])
    assert float(stored.price_review["anchor"]["price"]) == 90
    assert stored.price_review["original"]["content_hash"] == doc.content_hash
    assert not db.query(ValuationModel).count() and not db.query(DcfAssumptionSet).count()
    assumptions[0].description="Updated wording"
    db.commit()
    assert client.post(root+"/decisions",json=frozen).json()["data"]["replayed"]
    assert client.post(root+"/decisions",json={**frozen,"reason":"Different"}).status_code==409
    assert client.post(root+"/decisions",json={**frozen,"request_id":str(uuid4())}).status_code==409
    none=client.post(root+"/decision-preview",json={**body,"original":None,"decision":"blocked"}).json()["data"]
    assert none["context"]["source_state"]=="none"
    app.dependency_overrides[get_current_user]=lambda: {"id":other.id}
    assert client.get(root+"/decision-options").status_code==404
    assert client.post(root+"/decisions",json=frozen).status_code==404
    assert db.query(ThesisChange).count()==1
