"""One visibility boundary for public coverage and owned processing history."""
from sqlalchemy import and_, func, or_

from app.models import ProcessingRun


def public_processing_run_filter():
    metadata = ProcessingRun.metadata_json
    return and_(
        func.coalesce(ProcessingRun.source_type, "").not_in(("private_upload", "user_source_labeled_csv")),
        ~ProcessingRun.run_type.startswith("brief_source", autoescape=True),
        ProcessingRun.run_type.not_in(("daily_brief_schedule", "portfolio_evidence_import", "valuation_source_refresh")),
        # Unowned legacy private attempts stay hidden, never assigned by guess.
        *(metadata[key].as_string().is_(None) for key in
          ("user_id", "portfolio_id", "brief_source_id", "schedule_id", "parent_run_id")),
    )


def visible_processing_run_filter(user_id: str):
    return or_(public_processing_run_filter(), ProcessingRun.metadata_json["user_id"].as_string() == user_id)
