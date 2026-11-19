from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.models import Company, MarketPrice, RawDocument, Source, ThesisNote
from app.models.user import User
from app.models.thesis_note import ThesisPricePin
from conftest import TEST_USER_ID


def company(db, ticker):
    row = Company(name=ticker, ticker=ticker, market="US")
    db.add(row)
    db.flush()
    return row


def close(db, issuer, day, price, **overrides):
    fields = dict(company_id=issuer.id, ticker=issuer.ticker, provider_symbol=issuer.ticker,
                  market="US", currency="USD", exchange="NASDAQ", provider_name="history",
                  price_type="end_of_day", adjustment_state="unadjusted", claim_type="Fact",
                  as_of_date=date.fromisoformat(day), price=Decimal(price))
    db.add(row := MarketPrice(**(fields | overrides)))
    db.flush()
    return row


def test_timeline_compares_like_closes_and_distinguishes_context(db, client):
    issuer, other = company(db, "AAA"), company(db, "BBB")
    db.add(source := Source(name="Filing register", source_type="filing"))
    db.flush()
    for owner in [issuer, other]:
        db.add(RawDocument(company_id=owner.id, source_id=source.id, title=owner.ticker + " filing",
                           document_type="sec_filing_metadata", content_hash=owner.ticker,
                           published_at=datetime(2026, 1, 6, tzinfo=timezone.utc)))
    close(db, issuer, "2026-01-05", "100")
    close(db, issuer, "2026-01-06", "95")
    close(db, issuer, "2026-01-07", "96")
    close(db, issuer, "2026-01-07", "97")
    close(db, issuer, "2026-01-08", "105")
    close(db, issuer, "2026-01-09", "300", currency="INR")
    close(db, issuer, "2026-01-12", "300", price_type="unknown")
    db.commit()
    data = client.get(f"/companies/{issuer.id}/price-timeline").json()["data"]
    assert data["series"]["currency"] == "USD" and len(data["choices"]) == 2
    points = data["points"]
    assert [p["date"] for p in points] == ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"]
    assert points[1]["large_move"] and points[1]["change_pct"] == -5
    assert [doc["title"] for doc in points[1]["sources"]] == ["AAA filing"]
    assert points[2]["price"] is None and points[3]["change_pct"] is None
    assert not points[0]["sources"]
    alternate = next(c for c in data["choices"] if c["currency"] == "INR")
    assert client.get(f"/companies/{issuer.id}/price-timeline", params={"series": alternate["key"]}).json()["data"]["points"][0]["price"] == 300


def test_pin_is_owned_retry_safe_and_retains_original_observation(db, client):
    issuer, other = company(db, "AAA"), company(db, "BBB")
    db.add(User(id="other-user", email="other@example.invalid", name="Other"))
    db.flush()
    def thesis(owner, stock):
        db.add(row := ThesisNote(user_id=owner, company_id=stock.id, title="Test thesis", thesis_text="Fixture"))
        db.flush()
        return row
    mine, theirs, wrong = thesis(TEST_USER_ID, issuer), thesis("other-user", issuer), thesis(TEST_USER_ID, other)
    price = close(db, issuer, "2026-01-06", "95")
    db.commit()
    base = f"/companies/{issuer.id}/price-timeline"
    point = client.get(base).json()["data"]["points"][0]
    payload = dict(thesis_id=mine.id, price_id=price.id, fingerprint=point["fingerprint"],
                   text="Check the disclosed assumption", request_id=str(uuid4()))
    for denied_note in [theirs, wrong]:
        assert client.post(base + "/pins", json=payload | {"thesis_id": denied_note.id}).status_code == 404
    assert client.get(f"/thesis-notes/{theirs.id}/price-pins").status_code == 404
    saved = client.post(base + "/pins", json=payload)
    assert saved.status_code in {200, 201}, saved.text
    pin = saved.json()["data"]
    db.add(ThesisPricePin(thesis_note_id=theirs.id, company_id=issuer.id, request_id=str(uuid4()),
                         fingerprint=point["fingerprint"], anchor=pin["anchor"], text="Other private note"))
    db.commit()
    assert client.post(base + "/pins", json=payload).json()["data"]["id"] == pin["id"]
    assert client.post(base + "/pins", json=payload | {"text": "Another text"}).status_code == 409
    assert len(client.get(base).json()["data"]["points"][0]["pins"]) == 1
    price.price = Decimal("98")
    db.commit()
    assert client.post(base + "/pins", json=payload | {"request_id": str(uuid4())}).status_code == 409
    assert client.get(base).json()["data"]["points"][0]["pins"] == []
    saved_pins = client.get(f"/thesis-notes/{mine.id}/price-pins").json()["data"]
    assert len(saved_pins) == 1 and saved_pins[0]["anchor"]["price"] == "95.000000"

    reassigned = client.patch(f"/thesis-notes/{mine.id}", json={"company_id": other.id})
    assert reassigned.status_code == 200, reassigned.text
    retained = client.get(f"/thesis-notes/{mine.id}/price-pins").json()["data"]
    assert len(retained) == 1 and retained[0]["company_id"] == issuer.id
    assert retained[0]["anchor"] == pin["anchor"]
    assert client.get(f"/thesis-notes/{theirs.id}/price-pins").status_code == 404


def test_empty_and_unknown_basis_and_long_gaps(db, client):
    issuer = company(db, "EMPTY")
    db.commit()
    base = f"/companies/{issuer.id}/price-timeline"
    assert client.get(base).json()["data"]["points"] == []
    assert client.get("/companies/999999/price-timeline").status_code == 404
    for d, p in [("2026-01-02", "10"), ("2026-01-05", "20"), ("2026-01-23", "40")]:
        close(db, issuer, d, p, adjustment_state="unknown")
    db.commit()
    assert all(p["change_pct"] is None for p in client.get(base).json()["data"]["points"])


def test_weekend_release_keeps_its_date_and_mock_series_cannot_displace_facts(db, client):
    issuer = company(db, "AAA")
    for day, price in [("2026-01-02", "100"), ("2026-01-05", "90"), ("2026-01-23", "120")]:
        close(db, issuer, day, price)
    for day in range(2, 7):
        close(db, issuer, f"2026-01-0{day}", "25", provider_name="example", claim_type="Mock Data")
    db.add(source := Source(name="Issuer releases", source_type="filing"))
    db.flush()
    for day in (4, 12):
        db.add(RawDocument(company_id=issuer.id, source_id=source.id, content_hash=f"day-{day}",
                           document_type="release", title="Issuer release",
                           published_at=datetime(2026, 1, day, 15, tzinfo=timezone.utc)))
    db.commit()
    result = client.get(f"/companies/{issuer.id}/price-timeline").json()["data"]
    assert result["series"]["claim_type"] == "Fact"
    assert result["points"][0]["sources"] == []
    assert result["points"][1]["sources"][0]["context_date"] == "2026-01-04"
    last = result["points"][-1]
    assert last["gap_before"] and last["sources"] == [] and last["change_pct"] is None
