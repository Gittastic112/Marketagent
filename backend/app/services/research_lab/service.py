"""Owned, immutable research receipts using the existing ProcessingRun ledger."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.processing_run import ProcessingRun
from app.schemas.research_lab import (
    AdapterCapability,
    ResearchCapabilities,
    ResearchRunManifest,
    ResearchRunResult,
    ResearchRunSummary,
)
from app.services.processing_runs import (
    complete_processing_run,
    fail_processing_run,
    start_processing_run,
)
from app.services.research_lab.common import digest, package_version
from app.services.research_lab.errors import ResearchAdapterError
from app.services.research_lab.runner import run_bounded


Kind = Literal["allocation", "simulation", "report", "peers"]
PACKAGES = (
    "PyPortfolioOpt",
    "bt",
    "quantstats",
    "numpy",
    "pandas",
    "scipy",
    "cvxpy",
    "clarabel",
)


def capabilities() -> ResearchCapabilities:
    adapters = [
        AdapterCapability(
            id="native",
            label="Equal weights and explicit simulations",
            available=True,
            version="1",
        )
    ]
    for package, label in (
        ("PyPortfolioOpt", "Constrained allocation and HRP"),
        ("bt", "Independent zero-cost simulation cross-check"),
        ("quantstats", "Return statistics and report export"),
    ):
        version = package_version(package)
        adapters.append(
            AdapterCapability(
                id=package,
                label=label,
                available=bool(version),
                version=version,
                reason=None if version else "Install the locked adapters profile.",
            )
        )
    snapshot = get_settings().research_peer_snapshot_path
    configured = bool(
        snapshot
        and Path(snapshot).is_file()
        and Path(snapshot + ".manifest.json").is_file()
    )
    adapters.append(
        AdapterCapability(
            id="FinanceDatabase",
            label="Local reference peer discovery",
            available=configured,
            version="snapshot/v1" if configured else None,
            reason="Snapshot checksum is verified on every run."
            if configured
            else "Configure a pinned local CSV and manifest.",
        )
    )
    return ResearchCapabilities(
        adapters=adapters,
        limits={
            "max_assets": 40,
            "max_observations": 2600,
            "worker_seconds": 40,
            "worker_concurrency": 2,
        },
        warnings=[
            "Capabilities show installed/configured components; a successful run also requires compatible inputs and Linux network isolation.",
            "No operation trades, edits holdings, approves financial candidates, or promotes peer sets.",
        ],
    )


def execute(
    db: Session, user_id: str, kind: Kind, request: BaseModel
) -> ResearchRunResult:
    inputs = request.model_dump(mode="json")
    input_hash = digest(inputs)
    run = start_processing_run(
        db,
        run_type=f"research_lab_{kind}",
        source_type="user_research_input",
        metadata={
            "user_id": user_id,
            "research_lab_version": "v1",
            "kind": kind,
            "input_sha256": input_hash,
            "input": inputs,
        },
    )
    try:
        if kind == "peers":
            result = run_bounded(
                kind,
                inputs,
                context={"snapshot_path": get_settings().research_peer_snapshot_path},
            )
        else:
            result = run_bounded(kind, inputs)
        now = datetime.now(timezone.utc)
        last_day = None
        if "dataset" in inputs:
            last_day = inputs["dataset"]["observations"][-1]["end_date"]
        elif kind == "report":
            last_day = inputs["returns"][-1]["date"]
        manifest = ResearchRunManifest(
            input_sha256=input_hash,
            output_sha256=digest(result),
            created_at=now,
            adapter=result["adapter"],
            adapter_version=result["adapter_version"],
            dependencies={
                name: version for name in PACKAGES if (version := package_version(name))
            },
            source_assertion="pinned_reference_snapshot"
            if kind == "peers"
            else "user_supplied_unverified",
            valuation_as_of=last_day,
            snapshot_created_at=now,
            knowledge_policy="reference_snapshot"
            if kind == "peers"
            else "unverified_research",
        )
        saved = ResearchRunResult(
            run_id=run.id,
            kind=kind,
            manifest=manifest,
            result=result,
            warnings=result.get("warnings", []),
        )
        complete_processing_run(
            db,
            run,
            created_count=1,
            metadata_patch={"research_result": saved.model_dump(mode="json")},
        )
        return saved
    except ResearchAdapterError as exc:
        db.rollback()
        fail_processing_run(db, run, error_type=exc.code, message=exc.message)
        exc.processing_run_id = run.id
        raise
    except Exception as exc:
        db.rollback()
        fail_processing_run(
            db,
            run,
            error_type="RESEARCH_ADAPTER_FAILED",
            message="The research adapter could not complete the request.",
        )
        failure = ResearchAdapterError(
            "RESEARCH_ADAPTER_FAILED",
            "The research adapter could not complete the request.",
            502,
        )
        failure.processing_run_id = run.id
        raise failure from exc


def _owned_query(user_id: str):
    return select(ProcessingRun).where(
        ProcessingRun.run_type.startswith("research_lab_", autoescape=True),
        ProcessingRun.metadata_json["user_id"].as_string() == user_id,
    )


def history(db: Session, user_id: str, limit: int = 25, before_run_id: int | None = None) -> list[ResearchRunSummary]:
    query = _owned_query(user_id)
    if before_run_id is not None:
        query = query.where(ProcessingRun.id < before_run_id)
    runs = db.scalars(
        query.order_by(ProcessingRun.id.desc()).limit(limit)
    ).all()
    summaries = []
    for run in runs:
        metadata = run.metadata_json or {}
        saved = metadata.get("research_result")
        manifest = saved.get("manifest") if isinstance(saved, dict) else None
        summaries.append(ResearchRunSummary(
            run_id=run.id,
            kind=metadata.get("kind") if isinstance(metadata.get("kind"), str) else "unknown",
            status=run.status,
            created_at=run.started_at,
            input_sha256=metadata.get("input_sha256") if isinstance(metadata.get("input_sha256"), str) else None,
            adapter=manifest.get("adapter") if isinstance(manifest, dict) and isinstance(manifest.get("adapter"), str) else None,
        ))
    return summaries


def saved_run(db: Session, user_id: str, run_id: int) -> dict:
    run = db.scalar(_owned_query(user_id).where(ProcessingRun.id == run_id))
    if run is None:
        raise ResearchAdapterError(
            "RESEARCH_RUN_NOT_FOUND", "Research run not found.", 404
        )
    metadata = run.metadata_json or {}
    if run.status != "success" or "research_result" not in metadata:
        raise ResearchAdapterError(
            "RESEARCH_RUN_INCOMPLETE",
            "This run has no completed result; inspect its Processing Run error.",
            409,
        )
    saved = metadata["research_result"]
    try:
        parsed = ResearchRunResult.model_validate(saved)
        if (
            type(saved["run_id"]) is not int or parsed.run_id != run.id
            or parsed.kind != metadata.get("kind")
            or run.run_type != f"research_lab_{parsed.kind}"
            or not isinstance(metadata.get("input"), dict)
            or parsed.manifest.adapter != parsed.result.get("adapter")
            or parsed.manifest.adapter_version != parsed.result.get("adapter_version")
        ):
            raise ValueError("Receipt identity is inconsistent")
        input_hash, output_hash = digest(metadata["input"]), digest(saved["result"])
    except (ValidationError, KeyError, TypeError, ValueError, OverflowError):
        raise ResearchAdapterError(
            "RESEARCH_RUN_INVALID", "The saved research receipt is incomplete or inconsistent. Its original record has been preserved.", 409
        ) from None
    if parsed.manifest.input_sha256 != input_hash or parsed.manifest.output_sha256 != output_hash or metadata.get("input_sha256") != input_hash:
        raise ResearchAdapterError(
            "RESEARCH_RUN_HASH_MISMATCH",
            "Stored research content no longer matches its receipt.",
            409,
        )
    return {"input": metadata["input"], **saved}
