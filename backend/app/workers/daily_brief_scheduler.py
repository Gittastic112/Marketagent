from __future__ import annotations

import argparse
import logging
import os
import time

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.daily_brief_schedule import run_due_daily_brief_schedules


logger = logging.getLogger(__name__)
DEFAULT_INTERVAL_SECONDS = 60
MINIMUM_INTERVAL_SECONDS = 15


def scheduler_interval_seconds() -> int:
    raw_value = os.getenv(
        "DAILY_BRIEF_SCHEDULER_INTERVAL_SECONDS",
        str(DEFAULT_INTERVAL_SECONDS),
    )
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS
    return max(value, MINIMUM_INTERVAL_SECONDS)


def run_worker_cycle() -> dict[str, int]:
    with SessionLocal() as db:
        result = run_due_daily_brief_schedules(db)
    if result["schedules_checked"] or result["failures"]:
        logger.info("Daily Brief scheduler cycle completed", extra=result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run due local Daily Brief schedules")
    parser.add_argument("--once", action="store_true", help="Run one due check and exit")
    args = parser.parse_args()
    configure_logging(get_settings().log_level)
    interval = scheduler_interval_seconds()
    logger.info(
        "Daily Brief scheduler started",
        extra={
            "interval_seconds": interval,
            "generation_mode": "deterministic_no_external_ai",
        },
    )
    while True:
        try:
            run_worker_cycle()
        except Exception:
            logger.exception("Daily Brief scheduler cycle failed")
        if args.once:
            return
        time.sleep(interval)


if __name__ == "__main__":
    main()
