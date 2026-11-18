"""Versioned calendar schedules with finite application coverage and explicit overrides."""
from datetime import date
from importlib.metadata import version
from zoneinfo import ZoneInfo

from app.providers.market_data.transport import provider_error, response_hash
from app.schemas.data_adapters import CalendarScheduleRequest, CalendarScheduleResult, CalendarSession

SUPPORTED = {
    "XNYS": ("NYSE", date(2000, 1, 1), date(2026, 12, 31)),
    "XNAS": ("NASDAQ", date(2000, 1, 1), date(2026, 12, 31)),
    "XNSE": ("NSE", date(1996, 1, 1), date(2026, 12, 31)),
    "XBOM": ("BSE", date(1997, 1, 1), date(2026, 12, 31)),
}
SUPPORTED_VERSION = "5.6.1"


def get_exchange_schedule(request: CalendarScheduleRequest) -> CalendarScheduleResult:
    try:
        import pandas_market_calendars as calendars
        import pandas as pd
    except ImportError:
        raise provider_error("exchange_calendar", "ADAPTER_DEPENDENCY_UNAVAILABLE",
            "Install the optional calendar adapter profile before requesting a schedule.", status=503) from None
    installed = version("pandas_market_calendars")
    if installed != SUPPORTED_VERSION:
        raise provider_error("exchange_calendar", "CALENDAR_VERSION_UNREVIEWED",
            "Calendar coverage must be reviewed for the installed version.", status=503)
    name, start, end = SUPPORTED[request.exchange]
    if request.start_date < start or request.end_date > end:
        raise provider_error("exchange_calendar", "CALENDAR_OUTSIDE_COVERAGE",
            "Requested dates are outside this calendar adapter's reviewed coverage range.", status=422)
    calendar = calendars.get_calendar(name)
    zone = ZoneInfo(str(calendar.tz))
    frame = calendar.schedule(start_date=request.start_date, end_date=request.end_date, tz="UTC", interruptions=True)
    sessions = {}
    for day, row in frame.iterrows():
        interruptions = []
        for column in frame.columns:
            if column.startswith("interruption_start_"):
                finish = column.replace("interruption_start_", "interruption_end_")
                if finish in row and not pd.isna(row[column]) and not pd.isna(row[finish]):
                    interruptions.append((row[column].to_pydatetime(), row[finish].to_pydatetime()))
        session = CalendarSession(date=day.date(), opens_at=row["market_open"].to_pydatetime(),
            closes_at=row["market_close"].to_pydatetime(), interruptions=interruptions)
        sessions[session.date] = session
    for override in request.overrides:
        if override.closed:
            sessions.pop(override.date, None)
        else:
            if (override.opens_at.astimezone(zone).date() != override.date
                    or override.closes_at.astimezone(zone).date() != override.date):
                raise provider_error("exchange_calendar", "CALENDAR_OVERRIDE_DATE_MISMATCH",
                    "Override times must fall on the declared market-local session date.", status=422)
            sessions[override.date] = CalendarSession(date=override.date, opens_at=override.opens_at,
                closes_at=override.closes_at, source="user_source_override", source_url=override.source_url)
    warnings = ["Calendar schedules are a versioned library interpretation, not confirmation from the exchange.",
                "Overrides are explicit user-source inputs; their linked announcements are not fetched or independently verified.",
                "Session count does not automatically determine return annualization."]
    if request.exchange in {"XNSE", "XBOM"}:
        warnings.append("Exceptional weekend sessions require explicit dated overrides; library weekday schedules can omit Muhurat or special sessions.")
    if request.exchange == "XNAS":
        warnings.append("The library's NASDAQ alias uses its NYSE calendar; venue-specific exceptions require overrides.")
    return CalendarScheduleResult(exchange=request.exchange, timezone=str(zone), library_version=installed,
        coverage_start=start, coverage_end=end,
        override_hash=response_hash([o.model_dump(mode="json") for o in request.overrides]),
        sessions=[sessions[d] for d in sorted(sessions)], warnings=warnings)
