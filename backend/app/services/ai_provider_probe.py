"""Explicit, audited connectivity check. Never sends application records to AI."""
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.hashing import sha256_text
from app.models.processing_run import ProcessingRun
from app.providers.ai_provider import DEFAULT_GEMINI_MODEL, GeminiAIProvider, GeminiRequestError


def probe_gemini(db: Session, *, model_name: str | None = None) -> dict:
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    model = model_name or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    # Validate configuration before storing an arbitrary model string in audit logs.
    provider = GeminiAIProvider(key, model_name=model)
    run = ProcessingRun(
        run_type="ai_provider_probe", source_type="gemini",
        started_at=datetime.now(timezone.utc), status="running",
        metadata_json={
            "provider": "gemini", "model": model, "configured": bool(key),
            "prompt_version": "connectivity-v1", "input_hash": sha256_text("Reply exactly OK."),
            "external_data_classes": ["fixed_connectivity_prompt"] if key else [],
            "source_ids": [], "is_mock": False,
            "limitations": "Connectivity only; does not certify research quality or future availability.",
        },
    )
    db.add(run)
    db.commit()
    code = None
    http_status = None
    try:
        if not key:
            code = "AI_PROVIDER_NOT_CONFIGURED"
        else:
            result = provider.check_connection()
            if result.output_text.strip() != "OK":
                code = "AI_PROBE_UNEXPECTED_RESPONSE"
    except GeminiRequestError as exc:
        http_status = exc.status_code
        code = {
            400: "AI_REQUEST_REJECTED", 401: "AI_AUTHENTICATION_FAILED",
            403: "AI_ACCESS_DENIED", 404: "AI_MODEL_UNAVAILABLE",
            429: "AI_RATE_LIMITED",
        }.get(http_status, "AI_PROVIDER_FAILED")
    except Exception:
        code = "AI_PROVIDER_FAILED"
    run.status = "failed" if code else "success"
    run.fetched_count = 0 if code else 1
    run.error_count = 1 if code else 0
    run.finished_at = datetime.now(timezone.utc)
    run.error_details_json = {"code": code, "message": code, "http_status": http_status} if code else None
    db.commit()
    return {"status": run.status, "model": model, "configured": bool(key),
            "processing_run_id": run.id, "failure_code": code, "http_status": http_status}
