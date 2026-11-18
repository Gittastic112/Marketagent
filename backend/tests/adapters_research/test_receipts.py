import hashlib
import json

import pytest

from app.models.processing_run import ProcessingRun
from app.services.research_lab import service
from app.services.research_lab.allocation import allocate
from app.schemas.research_lab import AllocationRequest, PeerDiscoveryRequest
from app.services.research_lab.errors import ResearchAdapterError
from app.services.research_lab.peers import discover
from .test_research_contracts import dataset_payload


def test_authenticated_run_saves_exact_input_hash_and_owned_export(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(
        service,
        "run_bounded",
        lambda kind, data: allocate(AllocationRequest.model_validate(data)),
    )
    request = {"dataset": dataset_payload(), "objective": "equal_weight"}
    response = client.post("/api/research-lab/allocation", json=request)
    assert response.status_code == 200, response.text
    saved = response.json()["data"]
    run_id = saved["run_id"]
    exported = client.get(f"/api/research-lab/runs/{run_id}/export")
    assert exported.status_code == 200
    assert exported.json()["input"] == AllocationRequest.model_validate(
        request
    ).model_dump(mode="json")
    assert exported.json()["manifest"]["public_information_cutoff"] is None
    assert exported.json()["manifest"]["source_assertion"] == "user_supplied_unverified"
    assert client.get("/api/research-lab/runs").json()["data"][0]["run_id"] == run_id
    with pytest.raises(ResearchAdapterError) as error:
        service.saved_run(db_session, "different-user", run_id)
    assert error.value.status_code == 404
    assert service.history(db_session, "different-user") == []
    html = client.get(f"/api/research-lab/runs/{run_id}/report.html")
    assert html.status_code == 200
    assert "sandbox" in html.headers["content-security-policy"]


def test_tampered_saved_input_or_output_blocks_export(client, db_session, monkeypatch):
    monkeypatch.setattr(
        service,
        "run_bounded",
        lambda kind, data: allocate(AllocationRequest.model_validate(data)),
    )
    response = client.post(
        "/api/research-lab/allocation",
        json={"dataset": dataset_payload(), "objective": "equal_weight"},
    )
    run = db_session.get(ProcessingRun, response.json()["data"]["run_id"])
    metadata = json.loads(json.dumps(run.metadata_json))
    metadata["input"]["dataset"]["source_label"] = "Changed after review"
    run.metadata_json = metadata
    db_session.commit()
    blocked = client.get(f"/api/research-lab/runs/{run.id}/export")
    assert blocked.status_code == 409
    assert blocked.json()["errors"][0]["code"] == "RESEARCH_RUN_HASH_MISMATCH"


@pytest.mark.parametrize("damage", ["run_id", "kind", "manifest", "result_shape", "input_shape", "adapter"])
def test_saved_receipt_rejects_malformed_or_misbound_content_without_rewriting(
    client, db_session, monkeypatch, damage
):
    monkeypatch.setattr(service, "run_bounded", lambda kind, data: allocate(AllocationRequest.model_validate(data)))
    response = client.post("/api/research-lab/allocation", json={"dataset": dataset_payload(), "objective": "equal_weight"})
    run = db_session.get(ProcessingRun, response.json()["data"]["run_id"])
    metadata = json.loads(json.dumps(run.metadata_json))
    saved = metadata["research_result"]
    if damage == "run_id":
        saved["run_id"] += 1000
    elif damage == "kind":
        saved["kind"] = "peers"
    elif damage == "manifest":
        del saved["manifest"]
    elif damage == "result_shape":
        metadata["research_result"] = ["Mock Data malformed receipt"]
    elif damage == "input_shape":
        metadata["input"] = None
    else:
        saved["manifest"]["adapter"] = "Mock Data mismatched adapter"
    run.metadata_json = metadata
    db_session.commit()
    for suffix in ("", "/export", "/report.html"):
        blocked = client.get(f"/api/research-lab/runs/{run.id}{suffix}")
        assert blocked.status_code == 409
        assert blocked.json()["errors"][0]["code"] == "RESEARCH_RUN_INVALID"
        assert "Mock Data" not in blocked.text
    db_session.expire_all()
    assert db_session.get(ProcessingRun, run.id).metadata_json == metadata
    assert client.get("/api/research-lab/runs").status_code == 200


def test_history_cursor_keeps_old_runs_reachable_and_owner_scoped(client, db_session, monkeypatch):
    monkeypatch.setattr(service, "run_bounded", lambda kind, data: allocate(AllocationRequest.model_validate(data)))
    request = AllocationRequest(dataset=dataset_payload(), objective="equal_weight")
    own_ids = [service.execute(db_session, "admin_user_id_fallback", "allocation", request).run_id for _ in range(5)]
    other = service.execute(db_session, "different-user", "allocation", request).run_id
    first = client.get("/api/research-lab/runs?limit=2").json()["data"]
    assert [row["run_id"] for row in first] == own_ids[-2:][::-1]
    service.execute(db_session, "admin_user_id_fallback", "allocation", request)
    second = client.get(f"/api/research-lab/runs?limit=2&before_run_id={first[-1]['run_id']}").json()["data"]
    third = client.get(f"/api/research-lab/runs?limit=2&before_run_id={second[-1]['run_id']}").json()["data"]
    assert [row["run_id"] for row in second + third] == own_ids[:-2][::-1]
    assert other not in [row["run_id"] for row in first + second + third]
    assert client.get("/api/research-lab/runs?before_run_id=0").status_code == 422


def test_missing_adapter_is_failure_receipt_not_mock_success(
    client, db_session, monkeypatch
):
    def unavailable(kind, data):
        raise ResearchAdapterError(
            "ADAPTER_DEPENDENCY_MISSING", "Install optional profile.", 503
        )

    monkeypatch.setattr(service, "run_bounded", unavailable)
    response = client.post(
        "/api/research-lab/allocation", json={"dataset": dataset_payload()}
    )
    assert response.status_code == 503
    error = response.json()["errors"][0]
    run = db_session.get(ProcessingRun, error["processing_run_id"])
    assert run.status == "failed"
    assert run.metadata_json["user_id"] == "admin_user_id_fallback"
    assert "research_result" not in run.metadata_json


def test_peer_search_uses_bounded_worker_and_excludes_server_path_from_receipt(
    client, monkeypatch
):
    from types import SimpleNamespace

    observed = []

    def local_worker(kind, data, *, context):
        observed.append((kind, data, context))
        return {
            "adapter": "FinanceDatabase_snapshot",
            "adapter_version": "1",
            "candidates": [],
            "warnings": [],
        }

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            research_peer_snapshot_path="/private/admin-configured.csv"
        ),
    )
    monkeypatch.setattr(service, "run_bounded", local_worker)
    response = client.post("/api/research-lab/peers", json={"country": "India"})
    assert response.status_code == 200, response.text
    assert observed[0][0] == "peers"
    assert observed[0][2] == {"snapshot_path": "/private/admin-configured.csv"}
    export = client.get(
        f"/api/research-lab/runs/{response.json()['data']['run_id']}/export"
    )
    assert "/private/" not in export.text


def test_snapshot_checks_hash_and_preserves_listing_ambiguity(tmp_path):
    path = tmp_path / "equities.csv"
    raw = b"symbol,name,currency,exchange,country,sector,industry,delisted\nA,Example,USD,NYQ,United States,Technology,Software,false\nA,Example ADR,USD,NMS,United States,Technology,Software,false\nD,Delisted,USD,NYQ,United States,Technology,Software,true\n"
    path.write_bytes(raw)
    manifest = {
        "source": "JerBouma/FinanceDatabase",
        "revision": "a" * 40,
        "observed_at": "2025-01-01T00:00:00+00:00",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    (tmp_path / "equities.csv.manifest.json").write_text(json.dumps(manifest))
    result = discover(PeerDiscoveryRequest(sector="Technology"), str(path))
    assert result["total_matches"] == 2
    assert {row["exchange"] for row in result["candidates"]} == {"NYQ", "NMS"}
    path.write_bytes(raw + b"\n")
    with pytest.raises(ResearchAdapterError, match="manifest"):
        discover(PeerDiscoveryRequest(), str(path))
