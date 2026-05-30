from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from typing import Any


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_FRONTEND_URL = "http://127.0.0.1:3000"


def join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def find_record(records: Iterable[dict[str, Any]], **criteria: object) -> dict[str, Any] | None:
    for record in records:
        if all(record.get(key) == value for key, value in criteria.items()):
            return record
    return None


def milestone_status(*, rss_feed_count: int, write_enabled: bool) -> dict[str, str]:
    if not write_enabled:
        return {"database_writes": "dry_run", "rss_live_feeds": "dry_run"}
    return {
        "database_writes": "enabled",
        "rss_live_feeds": "ready" if rss_feed_count >= 3 else "needs_3_feeds",
    }


def request_json(
    method: str,
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        join_url(base_url, path),
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        try:
            parsed = json.loads(detail)
            if isinstance(parsed, dict) and parsed.get("detail"):
                detail = str(parsed["detail"])
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"{method} {path} failed with {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {path} failed: {exc.reason}") from exc


def request_ok(method: str, url: str, timeout: int = 10) -> None:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"{method} {url} failed with {response.status}")


def check(label: str, fn) -> bool:
    try:
        fn()
    except Exception as exc:
        print(f"FAIL {label}: {exc}")
        return False
    print(f"PASS {label}")
    return True


def get_or_create_source(
    backend_url: str,
    *,
    name: str,
    source_type: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    sources = request_json("GET", backend_url, "/sources")
    existing = find_record(sources, name=name, source_type=source_type)
    if existing is not None:
        return existing
    return request_json(
        "POST",
        backend_url,
        "/sources",
        {
            "name": name,
            "source_type": source_type,
            "base_url": base_url,
            "reliability_score": 95 if source_type == "sec" else 70,
            "active": True,
        },
    )


def get_or_create_company(backend_url: str, ticker: str) -> dict[str, Any]:
    normalized_ticker = ticker.upper()
    companies = request_json("GET", backend_url, "/companies")
    existing = find_record(companies, ticker=normalized_ticker)
    if existing is not None:
        if existing.get("cik"):
            return existing
        lookup = request_json("GET", backend_url, f"/companies/lookup?ticker={urllib.parse.quote(normalized_ticker)}")
        return request_json(
            "PATCH",
            backend_url,
            f"/companies/{existing['id']}",
            {
                "ticker": lookup["ticker"],
                "name": lookup["name"],
                "cik": lookup["cik"],
            },
        )

    lookup = request_json("GET", backend_url, f"/companies/lookup?ticker={urllib.parse.quote(normalized_ticker)}")
    return request_json(
        "POST",
        backend_url,
        "/companies",
        {
            "ticker": lookup["ticker"],
            "name": lookup["name"],
            "cik": lookup["cik"],
            "active": True,
        },
    )


def verify_write_workflow(args: argparse.Namespace) -> None:
    company = get_or_create_company(args.backend_url, args.ticker)
    sec_source = get_or_create_source(args.backend_url, name="SEC EDGAR", source_type="sec")

    preview_path = (
        f"/companies/{company['id']}/sec-filings/preview?"
        f"form_type={urllib.parse.quote(args.form_type)}&limit=1"
    )
    if args.filing_year is not None:
        preview_path += f"&filing_year={args.filing_year}"
    filings = request_json("GET", args.backend_url, preview_path)
    if not filings:
        raise RuntimeError(f"No SEC filings returned for {company['ticker']} {args.form_type}")

    ingest_result = request_json(
        "POST",
        args.backend_url,
        "/ingest/sec-filings",
        {
            "source_id": sec_source["id"],
            "company_id": company["id"],
            "filings": [filings[0]],
            "download_text": args.download_text,
        },
        timeout=60,
    )
    if ingest_result["error_count"] != 0:
        raise RuntimeError(f"SEC ingestion returned errors: {ingest_result['errors']}")
    if ingest_result["fetched_count"] < 1:
        raise RuntimeError("SEC ingestion did not fetch a filing")

    events = request_json("GET", args.backend_url, "/events")
    linked_events = [event for event in events if event.get("company_id") == company["id"]]
    if not linked_events:
        raise RuntimeError("No linked events found after SEC ingestion")
    if not any(event.get("priority_score") is not None for event in linked_events):
        raise RuntimeError("Linked events exist, but none have scoring fields")

    alerts = request_json("GET", args.backend_url, "/alerts")
    linked_alerts = [alert for alert in alerts if alert.get("company_id") == company["id"]]
    if not linked_alerts:
        raise RuntimeError("No linked alerts found after SEC ingestion")

    request_json("POST", args.backend_url, "/daily-brief")

    if len(args.rss_feed) < 3:
        raise RuntimeError("Provide at least three --rss-feed values to finish RSS live verification")

    for index, feed_url in enumerate(args.rss_feed, start=1):
        source = get_or_create_source(
            args.backend_url,
            name=f"Milestone A RSS {index}",
            source_type="rss",
            base_url=feed_url,
        )
        result = request_json(
            "POST",
            args.backend_url,
            "/ingest/rss-feed",
            {"source_id": source["id"], "feed_url": feed_url},
            timeout=60,
        )
        if result["error_count"] != 0:
            raise RuntimeError(f"RSS feed {feed_url} returned errors: {result['errors']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Milestone A against a running local app.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--form-type", default="10-K")
    parser.add_argument("--filing-year", type=int)
    parser.add_argument("--rss-feed", action="append", default=[])
    parser.add_argument("--download-text", action="store_true")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create or reuse local verification records and run SEC/RSS ingestion.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    status = milestone_status(rss_feed_count=len(args.rss_feed), write_enabled=args.write)
    print(f"database_writes={status['database_writes']}")
    print(f"rss_live_feeds={status['rss_live_feeds']}")

    checks = [
        check("backend health", lambda: request_json("GET", args.backend_url, "/health")),
        check("frontend reachable", lambda: request_ok("GET", args.frontend_url)),
        check(
            f"ticker lookup {args.ticker}",
            lambda: request_json("GET", args.backend_url, f"/companies/lookup?ticker={urllib.parse.quote(args.ticker.upper())}"),
        ),
    ]

    if args.write:
        checks.append(check("SEC/RSS write workflow", lambda: verify_write_workflow(args)))
    else:
        print("SKIP write workflow: run again with --write after you are comfortable creating local verification records")

    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
