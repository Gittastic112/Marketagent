import asyncio
import logging
import re
from typing import Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.financial import FinancialStatementPeriod, FinancialMetric
from app.services.sec_xbrl_extractor import fetch_company_facts

logger = logging.getLogger(__name__)

SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

WHITELISTED_METRICS = {
    "Revenues": "Revenue",
    "NetIncomeLoss": "Net Income",
    "EarningsPerShareBasic": "EPS (Basic)",
    "Assets": "Total Assets",
    "Liabilities": "Total Liabilities",
    "StockholdersEquity": "Stockholders Equity"
}

async def fetch_sec_company_facts(cik: str) -> dict[str, Any]:
    """Compatibility import; share bounded transport and propagate explicit failure."""
    return await asyncio.to_thread(fetch_company_facts, cik)

def process_sec_facts(db: Session, company_id: int, facts_data: dict[str, Any]) -> tuple[int, int]:
    """
    Legacy internal writer, retained for import compatibility only. HTTP intake
    uses sec_xbrl_ingestion and never calls this unreviewed write path.
    Processes raw SEC facts JSON and populates FinancialStatementPeriod and FinancialMetric tables.
    Returns (periods_created, metrics_created).
    """
    if not facts_data or "facts" not in facts_data or "us-gaap" not in facts_data["facts"]:
        return 0, 0

    company = db.get(Company, company_id)
    if company is None:
        return 0, 0

    gaap_facts = facts_data["facts"]["us-gaap"]

    # Track existing periods to avoid duplicates and map them
    # Key: (year, quarter, period_type)
    # Value: FinancialStatementPeriod
    existing_periods_query = select(FinancialStatementPeriod).where(FinancialStatementPeriod.company_id == company_id)
    existing_periods = {
        (p.year, p.quarter, p.period_type): p
        for p in db.execute(existing_periods_query).scalars().all()
    }

    periods_created = 0
    metrics_created = 0

    for gaap_concept, metric_name in WHITELISTED_METRICS.items():
        if gaap_concept not in gaap_facts:
            continue

        units = gaap_facts[gaap_concept].get("units", {})
        # Usually USD or shares/EPS
        primary_unit = "USD"
        if "USD" in units:
            fact_list = units["USD"]
        elif "USD/shares" in units:
            fact_list = units["USD/shares"]
            primary_unit = "USD/shares"
        else:
            # Fallback to first available unit
            if not units:
                continue
            first_unit = list(units.keys())[0]
            fact_list = units[first_unit]
            primary_unit = first_unit

        for fact in fact_list:
            # Ignore facts that don't have a specific timeframe, or are projections
            if "frame" not in fact:
                continue

            frame = fact["frame"] # e.g. "CY2020", "CY2020Q1"
            if not frame.startswith("CY"):
                continue

            val = fact.get("val")
            if val is None:
                continue

            # Parse frame
            # CY2020 -> Annual
            # CY2020Q1 -> Quarterly
            year = int(frame[2:6])
            quarter = None
            period_type = "annual"

            if len(frame) == 8 and frame[6] == "Q":
                quarter = int(frame[7])
                period_type = "quarterly"

            end_date_str = fact.get("end")
            try:
                report_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except:
                continue

            period_key = (year, quarter, period_type)
            period = existing_periods.get(period_key)
            unit_match = re.match(r"([A-Z]{3})\b", primary_unit.upper())
            unit_currency = unit_match.group(1) if unit_match else None
            reporting_currency = unit_currency or company.currency or "USD"
            currency_source = "sec_xbrl_unit" if unit_currency else ("company_fallback" if company.currency else "system_default")
            currency_confidence = "high" if unit_currency else "low"

            if not period:
                period = FinancialStatementPeriod(
                    company_id=company_id,
                    period_type=period_type,
                    year=year,
                    quarter=quarter,
                    report_date=report_date,
                    currency=reporting_currency,
                    currency_source=currency_source,
                    currency_confidence=currency_confidence,
                )
                db.add(period)
                db.flush() # get ID
                existing_periods[period_key] = period
                periods_created += 1
            elif unit_currency and period.currency != unit_currency:
                logger.warning(
                    "Skipping SEC fact with currency %s for period %s already recorded as %s",
                    unit_currency,
                    period.id,
                    period.currency,
                )
                continue
            elif unit_currency and period.currency_source in {"legacy_unknown", "company_fallback", "system_default"}:
                period.currency = unit_currency
                period.currency_source = "sec_xbrl_unit"
                period.currency_confidence = "high"

            # Check if metric already exists for this period
            # For simplicity, we just delete existing metrics of the same name and recreate, or check
            # Since we flush, period.metrics might be empty list initially. We query DB.
            existing_metric = db.execute(
                select(FinancialMetric).where(
                    FinancialMetric.period_id == period.id,
                    FinancialMetric.metric_name == metric_name
                )
            ).scalars().first()

            if not existing_metric:
                metric = FinancialMetric(
                    period_id=period.id,
                    metric_name=metric_name,
                    value=float(val),
                    unit=primary_unit
                )
                db.add(metric)
                metrics_created += 1
            else:
                existing_metric.value = float(val)
                existing_metric.unit = primary_unit

    db.commit()
    return periods_created, metrics_created
