"""One explicit connectivity check, recorded separately from data ingestion."""
import argparse
import json

from app.db.session import SessionLocal
from app.services.market_data.base import MarketDataRequest
from app.services.provider_connectivity import probe_public_provider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=["sec", "fred", "market"])
    parser.add_argument("--ticker")
    parser.add_argument("--market", choices=["US", "IN"])
    parser.add_argument("--exchange")
    parser.add_argument("--currency")
    args = parser.parse_args()
    if args.provider != "fred" and (not args.ticker or not args.market):
        parser.error("SEC and market probes require an explicit ticker and market")
    request = MarketDataRequest(ticker=args.ticker, market=args.market,
        exchange=args.exchange, currency=args.currency) if args.ticker and args.market else None
    with SessionLocal() as db:
        result = probe_public_provider(db, args.provider, request=request)
    print(json.dumps(result))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
