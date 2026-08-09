import pytest
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.narrative import NarrativeCluster, NarrativeClaim, NarrativeMention
from app.services.narrative_extraction import extract_narratives_from_events

def test_extract_narratives_mock(db: Session):
    # Create a mock event
    event = Event(
        title="Test Event for Narrative",
        description="This event is used to test narrative extraction.",
        event_type="test",
        information_speed="fast",
        credibility_score=5,
        novelty_score=5,
        impact_score=5,
        priority_score=5,
        data_confidence_score=5,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    result = extract_narratives_from_events(
        db,
        user_id="admin_user_id_fallback",
    )

    assert result.created_clusters == 1
    assert result.created_claims == 1
    assert result.created_mentions == 1

    # Verify database state
    mentions = list(db.query(NarrativeMention).all())
    assert len(mentions) == 1
    assert mentions[0].event_id == event.id

    clusters = list(db.query(NarrativeCluster).all())
    assert len(clusters) == 1
    assert clusters[0].id == mentions[0].cluster_id

    claims = list(db.query(NarrativeClaim).all())
    assert len(claims) == 1
    assert claims[0].cluster_id == clusters[0].id

    # Run again, should not duplicate
    result2 = extract_narratives_from_events(
        db,
        user_id="admin_user_id_fallback",
    )
    assert result2.created_clusters == 0
    assert result2.created_claims == 0
    assert result2.created_mentions == 0
