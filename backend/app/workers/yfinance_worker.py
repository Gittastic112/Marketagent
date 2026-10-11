"""Ephemeral SDK process. It receives public security identity, never app secrets."""
import json
import sys

from app.services.market_data.yfinance_jobs import CPU_SECONDS, MAX_OUTPUT_BYTES, MEMORY_BYTES


def apply_limits(*, cpu_seconds: int = CPU_SECONDS, memory_bytes: int = MEMORY_BYTES) -> None:
    import resource
    for kind, limit in ((resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1)),
        (resource.RLIMIT_AS, (memory_bytes, memory_bytes)),
        (resource.RLIMIT_FSIZE, (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES)),
        (resource.RLIMIT_CORE, (0, 0)), (resource.RLIMIT_NOFILE, (64, 64))):
        resource.setrlimit(kind, limit)


def main() -> None:
    try:
        apply_limits()
        raw = sys.stdin.buffer.read(4097)
        if len(raw) > 4096:
            raise ValueError("Input limit")
        job = json.loads(raw)
        from app.providers.market_data.yfinance_provider import YFinanceMarketProvider
        from app.services.market_data.base import MarketDataRequest
        request = MarketDataRequest.model_validate(job["request"])
        provider = YFinanceMarketProvider()
        if job["mode"] == "quote":
            result = provider._fetch_quote(request).model_dump(mode="json")
        elif job["mode"] == "history" and 1 <= job["days"] <= 3650:
            result = [row.model_dump(mode="json") for row in provider._fetch_history(request, job["days"])]
        else:
            raise ValueError("Invalid operation")
        encoded = json.dumps({"data": result}, allow_nan=False).encode()
        if len(encoded) > MAX_OUTPUT_BYTES:
            raise ValueError("Output limit")
        sys.stdout.buffer.write(encoded)
    except Exception:
        # SDK errors can contain remote responses; use a fixed category only.
        print('{"error":"unavailable"}')


if __name__ == "__main__":
    main()
