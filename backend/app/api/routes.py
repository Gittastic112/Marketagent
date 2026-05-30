from fastapi import APIRouter

from app.api.routers import (
    alerts,
    companies,
    daily_brief,
    events,
    ingestion,
    manual_processing,
    market_prices,
    market,
    portfolios,
    processing_runs,
    raw_documents,
    sources,
    thesis_notes,
    fundamentals,
    valuations,
    social,
    scoring_config,
    macro,
    exposure_tags,
    data_transfer,
    oauth,
    research,
)


router = APIRouter()

for route_group in (
    companies.router,
    sources.router,
    raw_documents.router,
    events.router,
    alerts.router,
    thesis_notes.router,
    daily_brief.router,
    portfolios.router,
    processing_runs.router,
    ingestion.router,
    manual_processing.router,
    market_prices.router,
    market.router,
    fundamentals.router,
    valuations.router,
    social.router,
    scoring_config.router,
    macro.router,
    exposure_tags.router,
    data_transfer.router,
    oauth.router,
    research.router,
):
    router.include_router(route_group)
