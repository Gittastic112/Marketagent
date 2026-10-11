import hashlib

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile


def test_list_damodaran_files_uses_import_timestamp(
    client: TestClient,
    db_session: Session,
) -> None:
    db_session.add(
        DamodaranDatasetFile(
            uploaded_filename="marginIndia.xls",
            dataset_code="margin",
            country="India",
            source_file_type="xls",
            source_sha256="a" * 64,
            source_byte_size=1234,
            source_as_of="2026-01-05",
            date_confidence="high",
            canonical_source_path="raw/datasets/marginIndia.xls",
            import_kind="typed",
            is_active=True,
            row_count=95,
            notes="Imported benchmark rows.",
        )
    )
    db_session.commit()

    response = client.get("/api/admin/damodaran/files")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["filename"] == "marginIndia.xls"
    assert data[0]["created_at"] is not None
    assert data[0]["source_sha256"] == "a" * 64
    assert data[0]["source_byte_size"] == 1234
    assert data[0]["source_as_of"] == "2026-01-05"
    assert data[0]["date_confidence"] == "high"
    assert data[0]["canonical_source_path"] == "raw/datasets/marginIndia.xls"
    assert data[0]["import_kind"] == "typed"
    assert data[0]["is_active"] is True
    assert data[0]["row_count"] == 95


def test_generic_admin_import_hashes_source_and_stays_metadata_only(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routers.admin_damodaran.parse_damodaran_workbook",
        lambda contents: {"Industry Averages": {"records": [{"Industry Name": "Advertising"}], "metadata": {}}},
    )
    # OLE header passes the intake preflight; the parser itself is mocked here.
    contents = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1generic-workbook-content"

    response = client.post(
        "/api/admin/damodaran/import",
        files={"file": ("roeIndia.xls", contents, "application/vnd.ms-excel")},
        data={"dataset_code": "roe", "country": "India"},
    )

    assert response.status_code == 200
    record = db_session.query(DamodaranDatasetFile).one()
    assert record.source_sha256 == hashlib.sha256(contents).hexdigest()
    assert record.source_byte_size == len(contents)
    assert record.source_as_of == "2026-01-05"
    assert record.date_confidence == "high"
    assert record.canonical_source_path == "raw/datasets/roeIndia(1).xls"
    assert record.import_kind == "metadata_only"
    assert record.is_active is False
    assert record.row_count is None


def test_typed_damodaran_version_cannot_be_deleted(
    client: TestClient,
    db_session: Session,
) -> None:
    record = DamodaranDatasetFile(
        uploaded_filename="roeIndia.xls",
        dataset_code="roe",
        country="India",
        source_file_type="xls",
        import_kind="typed",
        is_active=True,
        row_count=94,
    )
    db_session.add(record)
    db_session.commit()

    response = client.post(f"/api/admin/damodaran/{record.id}/rollback", json={})

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "DAMODARAN_VERSION_DELETE_BLOCKED"
    assert db_session.get(DamodaranDatasetFile, record.id) is not None
