"""Durable public-source queue worker. No external AI and no valuation approval."""
import argparse
import logging
import time

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.valuation_source_refresh import run_refresh_cycle

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run queued and weekday valuation source refreshes")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    configure_logging(get_settings().log_level)
    while True:
        try:
            with SessionLocal() as db:
                result = run_refresh_cycle(db)
            if result["processed"]:
                logger.info("Valuation source refresh cycle finished", extra=result)
        except Exception:
            # Provider exception bodies may contain credential-bearing request URLs.
            logger.error("Valuation source worker cycle failed; check local database readiness")
        if args.once:
            return
        time.sleep(30)


if __name__ == "__main__":
    main()
