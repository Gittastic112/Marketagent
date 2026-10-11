import csv
from datetime import date
from hashlib import sha256
from io import StringIO

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Company, PeerValuationSet, User
from app.services import peer_valuation_import
from app.services.peer_valuation_import import (
    LEGACY_PEER_CSV_COLUMNS,
    PEER_CSV_COLUMNS,
    PeerCsvApplyRequest,
    apply_peer_csv,
)
from app.services.peer_valuation_sets import PeerMemberInput, PeerValuationSetCreate, PeerValuationSetService
from helpers import response_data


def _csv_text(*, set_name: str = "Receipt test", legacy: bool = False) -> str:
    columns = LEGACY_PEER_CSV_COLUMNS if legacy else PEER_CSV_COLUMNS
    rows = [dict.fromkeys(columns, "") for _ in range(3)]
    for index, row in enumerate(rows):
        row.update(
            set_name=set_name,
            identifier=f"IDEM{index}",
            included="true",
            source_name="Issuer filing",
            source_url="https://example.com/filing",
            source_as_of=date.today().isoformat(),
            claim_type="Fact",
            pe=str(10 + index),
        )
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _apply(client, company_id: int, csv_text: str):
    return client.post(
        "/api/valuation/relative/peer-sets/import/apply",
        json={
            "companyId": company_id,
            "csvText": csv_text,
            "expectedSha256": sha256(csv_text.encode("utf-8")).hexdigest(),
        },
    )


@pytest.fixture
def target_company(db_session):
    company = Company(ticker="IDEM", name="Idempotency target", market="US")
    db_session.add(company)
    db_session.commit()
    return company


@pytest.mark.parametrize("legacy", [False, True])
def test_repeated_exact_csv_apply_reuses_one_set_and_revision(
    client, db_session, target_company, legacy
):
    csv_text = _csv_text(legacy=legacy)

    first = _apply(client, target_company.id, csv_text)
    second = _apply(client, target_company.id, csv_text)

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = response_data(first)
    second_data = response_data(second)
    assert first_data["importDisposition"] == "created"
    assert second_data["importDisposition"] == "reused"
    assert second_data["id"] == first_data["id"]
    assert second_data["importSha256"] == sha256(csv_text.encode("utf-8")).hexdigest()
    assert db_session.query(PeerValuationSet).count() == 1
    assert len(db_session.get(PeerValuationSet, first_data["id"]).revisions) == 1


def test_changed_csv_creates_a_new_receipt(client, db_session, target_company):
    first = response_data(_apply(client, target_company.id, _csv_text(set_name="First")))
    second = response_data(_apply(client, target_company.id, _csv_text(set_name="Second")))

    assert first["id"] != second["id"]
    assert second["importDisposition"] == "created"
    assert db_session.query(PeerValuationSet).count() == 2


def test_receipt_is_scoped_to_owner_and_target_company(db_session, target_company):
    other_company = Company(ticker="IDEM2", name="Second target", market="US")
    other_user = User(id="other-user", email="other@example.com", name="Other")
    db_session.add_all([other_company, other_user])
    db_session.commit()
    csv_text = _csv_text()
    digest = sha256(csv_text.encode("utf-8")).hexdigest()

    first = apply_peer_csv(
        db_session,
        user_id="admin_user_id_fallback",
        payload=PeerCsvApplyRequest(
            companyId=target_company.id, csvText=csv_text, expectedSha256=digest
        ),
    )
    other_target = apply_peer_csv(
        db_session,
        user_id="admin_user_id_fallback",
        payload=PeerCsvApplyRequest(
            companyId=other_company.id, csvText=csv_text, expectedSha256=digest
        ),
    )
    other_owner = apply_peer_csv(
        db_session,
        user_id=other_user.id,
        payload=PeerCsvApplyRequest(
            companyId=target_company.id, csvText=csv_text, expectedSha256=digest
        ),
    )

    assert len({first["id"], other_target["id"], other_owner["id"]}) == 3
    assert db_session.query(PeerValuationSet).count() == 3


def test_retry_reuses_archived_set_without_reactivating(client, db_session, target_company):
    csv_text = _csv_text()
    created = response_data(_apply(client, target_company.id, csv_text))
    peer_set = db_session.get(PeerValuationSet, created["id"])
    peer_set.is_active = False
    db_session.commit()

    retried = response_data(_apply(client, target_company.id, csv_text))

    assert retried["id"] == created["id"]
    assert retried["importDisposition"] == "reused"
    assert retried["isActive"] is False
    assert db_session.query(PeerValuationSet).count() == 1


def test_concurrent_unique_collision_returns_winning_receipt(
    client, db_session, target_company, monkeypatch
):
    csv_text = _csv_text()
    winning = response_data(_apply(client, target_company.id, csv_text))
    winning_set = db_session.get(PeerValuationSet, winning["id"])
    lookups = iter([None, winning_set])
    monkeypatch.setattr(peer_valuation_import, "_existing_import", lambda *args, **kwargs: next(lookups))

    def collide(*args, **kwargs):
        raise IntegrityError("INSERT", {}, RuntimeError("unique collision"))

    monkeypatch.setattr(PeerValuationSetService, "create_set", collide)
    retried = apply_peer_csv(
        db_session,
        user_id="admin_user_id_fallback",
        payload=PeerCsvApplyRequest(
            companyId=target_company.id,
            csvText=csv_text,
            expectedSha256=sha256(csv_text.encode("utf-8")).hexdigest(),
        ),
    )

    assert retried["id"] == winning["id"]
    assert retried["importDisposition"] == "reused"


def test_manual_sets_keep_nullable_receipts(db_session, target_company):
    member = PeerMemberInput(
        identifier="MANUAL",
        sourceName="Issuer filing",
        sourceUrl="https://example.com/filing",
        sourceAsOf=date.today(),
        multiples={"pe": 12},
    )
    payload = PeerValuationSetCreate(companyId=target_company.id, name="Manual", members=[member])

    first = PeerValuationSetService.create_set(
        db_session, user_id="admin_user_id_fallback", payload=payload
    )
    second = PeerValuationSetService.create_set(
        db_session, user_id="admin_user_id_fallback", payload=payload
    )

    assert first.import_sha256 is None
    assert second.import_sha256 is None
    assert first.id != second.id
