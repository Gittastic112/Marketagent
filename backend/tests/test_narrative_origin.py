"""New claims retain exact origin; legacy rows are never inferred or rewritten."""
from sqlalchemy import select

from app.models import Event, User
from app.models.ai import AiOutput
from app.models.narrative import NarrativeClaim, NarrativeCluster
from app.api.dependencies import get_current_user
from app.main import app
from app.services.narrative_extraction import extract_narratives_from_events
from conftest import TEST_USER_ID


def test_generated_claim_tracks_exact_output_without_exposing_another_owners_output(client, db):
    event = Event(title="Mock Data narrative", description="Mock Data evidence", event_type="test", information_speed="slow")
    db.add(event); db.commit()
    extract_narratives_from_events(db, user_id=TEST_USER_ID)
    claim = db.scalar(select(NarrativeClaim))
    output = db.scalar(select(AiOutput))
    own = client.get(f"/narrative-claims/{claim.id}").json()["data"]
    assert own["origin"] == "mock"
    assert own["ai_output"]["id"] == output.id
    assert own["ai_output"]["input_hash"] == output.input_hash
    for state in ["pending", "rejected", "approved"]:
        output.human_review_status = state; db.commit()
        assert client.get(f"/narrative-claims/{claim.id}").json()["data"]["ai_output"]["human_review_status"] == state
    assert client.patch(f"/narrative-claims/{claim.id}", json={"claim_text":"Changed claim"}).status_code == 409
    db.add(User(id="narrative-other", email="other@example.invalid", name="Other")); db.commit()
    app.dependency_overrides[get_current_user] = lambda: {"id":"narrative-other"}
    foreign = client.get(f"/narrative-claims/{claim.id}").json()["data"]
    assert foreign["origin"] == "mock" and foreign["ai_output"] is None
    assert "input_hash" not in str(foreign) and "ai_output_id" not in foreign


def test_manual_and_unknown_legacy_origins_remain_distinct(client, db):
    cluster = NarrativeCluster(name="Mock Data origin labels")
    db.add(cluster); db.flush()
    legacy = NarrativeClaim(cluster_id=cluster.id, claim_text="Existing claim")
    db.add(legacy); db.commit()
    manual = client.post("/narrative-claims", json={"cluster_id":cluster.id,"claim_text":"New manual claim"}).json()["data"]
    assert manual["origin"] == "manual" and manual["ai_output"] is None
    read = client.get(f"/narrative-claims/{legacy.id}").json()["data"]
    assert read["origin"] == "legacy_unknown" and read["ai_output"] is None
    assert db.get(NarrativeClaim, legacy.id).claim_text == "Existing claim"
