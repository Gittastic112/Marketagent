"""Single-use PDF parser. No database/provider credentials are passed to it."""
from __future__ import annotations

import base64
from dataclasses import asdict
import json
import sys

from app.services.pdf_jobs import CPU_SECONDS, MAX_INPUT_BYTES, MAX_OUTPUT_BYTES, MEMORY_BYTES


def apply_limits(*, cpu_seconds: int = CPU_SECONDS, memory_bytes: int = MEMORY_BYTES) -> None:
    import resource

    for kind, limits in ((resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1)),
        (resource.RLIMIT_AS, (memory_bytes, memory_bytes)),
        (resource.RLIMIT_FSIZE, (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES)),
        (resource.RLIMIT_CORE, (0, 0)), (resource.RLIMIT_NOFILE, (64, 64))):
        resource.setrlimit(kind, limits)


def main() -> None:
    try:
        apply_limits()
    except (ImportError, OSError, ValueError):
        print(json.dumps({"error": {"code": "unavailable"}}))
        return
    try:
        header = sys.stdin.buffer.readline(4097)
        if len(header) > 4096 or not header.endswith(b"\n"):
            raise ValueError("Invalid header")
        job = json.loads(header)
        content = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(content) > MAX_INPUT_BYTES or not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF body")
        options = job["options"]
        mode = job["mode"]
        if mode == "financial":
            from app.services.pdf_financial_extraction import _parse_pdf_financial_tables
            parsed = _parse_pdf_financial_tables(content, page_numbers=tuple(options["page_numbers"]) if options.get("page_numbers") is not None else None,
                period_type=options["period_type"])
            result = asdict(parsed)
        elif mode == "brief":
            from app.services.brief_source_extraction import _extract_brief_pdf
            result = _extract_brief_pdf("source.pdf", "application/pdf", content, options.get("page_ranges"))
        elif mode in {"size", "render"}:
            from app.services.pdf_page_rendering import _get_pdf_page_size, _render_pdf_page_png
            result = _get_pdf_page_size(content, options["page_number"]) if mode == "size" else base64.b64encode(
                _render_pdf_page_png(content, options["page_number"], options["scale"])).decode("ascii")
        else:
            raise ValueError("Invalid operation")
        encoded = json.dumps({"data": result}, allow_nan=False).encode()
        if len(encoded) > MAX_OUTPUT_BYTES:
            raise MemoryError("Result limit")
        sys.stdout.buffer.write(encoded)
    except MemoryError:
        print(json.dumps({"error": {"code": "limits"}}))
    except Exception as error:
        # Return categories only. Raw exception details, paths and source text
        # never cross this process boundary or enter application logs.
        code = "too_large" if getattr(error, "status_code", None) == 413 else "invalid"
        detail = getattr(error, "detail", "")
        if isinstance(detail, str) and detail.startswith("No usable text layer"):
            code = "no_text"
        print(json.dumps({"error": {"code": code}}))


if __name__ == "__main__":
    main()
