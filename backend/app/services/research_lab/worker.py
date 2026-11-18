"""Bounded local calculation worker. Input and output are JSON, never code."""

import contextlib
import json
import resource
import sys

from app.schemas.research_lab import (
    AllocationRequest,
    PeerDiscoveryRequest,
    ReportRequest,
    SimulationRequest,
)
from app.services.research_lab.errors import ResearchAdapterError


def dispatch(kind: str, data: dict, context: dict | None = None) -> dict:
    if kind == "peers":
        from app.services.research_lab.peers import discover

        return discover(
            PeerDiscoveryRequest.model_validate(data),
            (context or {}).get("snapshot_path"),
        )
    if kind == "allocation":
        from app.services.research_lab.allocation import allocate

        return allocate(AllocationRequest.model_validate(data))
    if kind == "simulation":
        from app.services.research_lab.simulation import simulate

        return simulate(SimulationRequest.model_validate(data))
    if kind == "report":
        from app.services.research_lab.reporting import report

        return report(ReportRequest.model_validate(data))
    raise ResearchAdapterError(
        "UNKNOWN_RESEARCH_OPERATION", "Unknown research operation."
    )


def main() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (25, 26))
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, 8 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        from app.providers.extraction.worker import deny_network

        deny_network()
    except (ImportError, OSError, ValueError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "RESEARCH_ISOLATION_UNAVAILABLE",
                        "message": "Local compute isolation is unavailable.",
                        "status_code": 503,
                    }
                }
            )
        )
        return
    raw = sys.stdin.buffer.read(4 * 1024**2 + 1)
    if len(raw) > 4 * 1024**2:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "RESEARCH_INPUT_TOO_LARGE",
                        "message": "Research input exceeds 4 MiB.",
                        "status_code": 413,
                    }
                }
            )
        )
        return
    try:
        payload = json.loads(raw)
        # Some scientific packages print progress. Protocol stdout remains JSON only.
        with contextlib.redirect_stdout(sys.stderr):
            result = dispatch(payload["kind"], payload["input"], payload.get("context"))
        print(json.dumps({"result": result}, allow_nan=False))
    except ResearchAdapterError as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "status_code": exc.status_code,
                    }
                }
            )
        )
    except Exception:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "RESEARCH_COMPUTE_FAILED",
                        "message": "The local research adapter could not complete these inputs.",
                        "status_code": 502,
                    }
                }
            )
        )


if __name__ == "__main__":
    main()
