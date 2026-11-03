import csv
import json
from datetime import date
from hashlib import sha256
from io import StringIO

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models import Company, PeerValuationSet
from app.services.peer_valuation_import import (
    PEER_CSV_COLUMNS,
    PeerCsvPreviewRequest,
    export_peer_csv,
    preview_peer_csv,
)
from app.services.peer_valuation_sets import PeerMemberInput, PeerValuationSetCreate
from helpers import response_data


def serialize(rows):
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=PEER_CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


@pytest.fixture
def csv_case(db_session):
    company = Company(ticker="SAFECSV", name="CSV test", market="US")
    db_session.add(company)
    db_session.commit()
    rows = [dict.fromkeys(PEER_CSV_COLUMNS, "") for _ in range(3)]
    for index, row in enumerate(rows):
        row.update(set_name="CSV safety", identifier=f"P{index}", included="true",
                   source_name="Issuer filing", source_url="https://example.com/filing",
                   source_as_of=date.today().isoformat(), claim_type="Fact", pe="12")
    return company.id, rows


@pytest.mark.parametrize("fault", ["extra_cell", "missing_cell", "quote", "large_field", "nul"])
def test_malformed_csv_is_blocked_without_writes(client, db_session, csv_case, fault):
    company_id, rows = csv_case
    text = serialize(rows)
    if fault in {"extra_cell", "missing_cell"}:
        parsed = list(csv.reader(StringIO(text)))
        if fault == "extra_cell":
            parsed[1].append("UNEXPECTED")
        else:
            parsed[1].pop()
        stream = StringIO(newline="")
        csv.writer(stream).writerows(parsed)
        text = stream.getvalue()
    elif fault == "quote":
        text += '"unterminated'
    elif fault == "large_field":
        rows[0]["notes"] = "x" * 200_000
        text = serialize(rows)
    else:
        text = text.replace("Issuer filing", "Issuer\x00filing")
    response = client.post("/api/valuation/relative/peer-sets/import/preview",
                           json={"companyId": company_id, "csvText": text})
    assert response.status_code == 200
    assert response_data(response)["isValid"] is False
    applied = client.post("/api/valuation/relative/peer-sets/import/apply", json={
        "companyId": company_id, "csvText": text,
        "expectedSha256": sha256(text.encode()).hexdigest(),
    })
    assert applied.status_code == 422
    assert db_session.query(PeerValuationSet).count() == 0


def test_utf8_byte_limit_stops_before_database_access():
    class NoDatabaseAccess:
        def get(self, *args):
            raise AssertionError("Oversized file must not query the database")

    result = preview_peer_csv(NoDatabaseAccess(), payload=PeerCsvPreviewRequest(
        companyId=1, csvText="界" * 400_000))
    assert result["isValid"] is False
    assert result["memberCount"] == 0
    assert "1 MB" in result["errors"][0]["message"]


@pytest.mark.parametrize("field,value", [
    ("set_name", "n" * 121), ("set_notes", "n" * 4001),
    ("set_name", "   "), ("set_notes", "DIFFERENT"),
])
def test_preview_validates_complete_create_metadata(db_session, csv_case, field, value):
    company_id, rows = csv_case
    for row in rows:
        row[field] = value
    if value == "DIFFERENT":
        rows[0][field] = ""
    result = preview_peer_csv(db_session, payload=PeerCsvPreviewRequest(
        companyId=company_id, csvText=serialize(rows)))
    assert result["isValid"] is False
    assert db_session.query(PeerValuationSet).count() == 0


def test_invalid_numeric_error_does_not_echo_uploaded_cell(db_session, csv_case):
    company_id, rows = csv_case
    rows[0]["pe"] = "PRIVATE_SENTINEL_DO_NOT_ECHO"
    result = preview_peer_csv(db_session, payload=PeerCsvPreviewRequest(
        companyId=company_id, csvText=serialize(rows)))
    assert result["isValid"] is False
    assert "PRIVATE_SENTINEL" not in json.dumps(result)
    assert result["errors"][0]["field"] == "pe"


def test_row_limit_is_bounded(db_session, csv_case):
    company_id, rows = csv_case
    result = preview_peer_csv(db_session, payload=PeerCsvPreviewRequest(
        companyId=company_id, csvText=serialize(rows * 17)))
    assert result["isValid"] is False
    assert result["memberCount"] <= 50


@pytest.mark.parametrize("audit", ["storageConsistency", "targetStorageConsistency"])
def test_export_refuses_conflicting_storage(audit):
    with pytest.raises(HTTPException) as exc:
        export_peer_csv({"id": 1, "version": 1, "name": "Conflict", "members": [],
                         audit: {"status": "mismatch"}})
    assert exc.value.status_code == 409


def test_export_preserves_literal_apostrophe_formula_text(client, db_session, csv_case):
    company_id, rows = csv_case
    result = export_peer_csv({"id": 1, "version": 1, "name": "'=literal", "members": [{
        "identifier": "TEST", "sourceName": "'=source", "sourceUrl": "https://example.com",
        "sourceAsOf": date.today().isoformat(), "claimType": "Fact", "multiples": {"pe": 12},
    }]})
    preview = preview_peer_csv(db_session, payload=PeerCsvPreviewRequest(
        companyId=company_id, csvText=result["csvText"]))
    assert preview["isValid"] is True
    assert preview["setName"] == "'=literal"
    assert preview["members"][0]["sourceName"] == "'=source"


@pytest.mark.parametrize("field", ["name", "sourceName"])
def test_direct_create_rejects_whitespace_identity(field):
    member = dict(identifier="P", sourceName="Issuer", sourceUrl="https://example.com",
                  sourceAsOf=date.today().isoformat(), multiples={"pe": 10})
    with pytest.raises(ValidationError):
        if field == "name":
            PeerValuationSetCreate(companyId=1, name="   ", members=[PeerMemberInput(**member)])
        else:
            PeerMemberInput(**{**member, "sourceName": "   "})
