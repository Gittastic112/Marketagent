import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import FinancialExtractionResultRead
from app.models import FinancialExtractionCandidate, RawDocument, FinancialMetric, FinancialStatementPeriod, Company
from app.models.company_setup import CompanySetupWorkflow
from app.services.accounting_normalization import MetricNormalizationEngine
from app.services.source_fact_history import record_financial_fact_revision


EXTRACTION_METHOD = "regex_line_item_v1"


@dataclass(frozen=True)
class MetricPattern:
    metric_code: str
    reported_label: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ReportingCurrencyResolution:
    currency: str | None
    source: str | None
    confidence: str


@dataclass(frozen=True)
class SourceLine:
    line_number: int
    text: str
    page: int | None
    section: str | None


METRIC_PATTERNS = (
    MetricPattern("revenue", "Revenue", ("revenue", "total revenue", "sales")),
    MetricPattern("ebit", "EBIT", ("ebit", "operating income")),
    MetricPattern("net_income", "Net income", ("net income", "profit after tax", "pat")),
    MetricPattern("cash", "Cash", ("cash and cash equivalents", "cash")),
    MetricPattern("debt", "Debt", ("total debt", "debt", "borrowings")),
    MetricPattern("capex", "Capex", ("capex", "capital expenditure", "capital expenditures")),
    MetricPattern(
        "depreciation",
        "Depreciation and amortization",
        ("depreciation and amortization", "depreciation", "d&a"),
    ),
    MetricPattern(
        "change_in_working_capital",
        "Change in working capital",
        ("change in working capital", "change in net working capital", "nwc change"),
    ),
    MetricPattern(
        "diluted_shares",
        "Diluted shares",
        (
            "weighted average diluted shares",
            "diluted weighted average shares",
            "diluted shares",
            "diluted share count",
            "shares outstanding",
        ),
    ),
    MetricPattern("basic_shares", "Basic shares", ("weighted average basic shares", "basic shares")),
    MetricPattern("acquisitions", "Acquisitions", ("business acquisitions", "acquisitions")),
    MetricPattern(
        "lease_liabilities",
        "Lease liabilities",
        ("operating lease liabilities", "lease liabilities"),
    ),
    MetricPattern(
        "minority_interests",
        "Minority interests",
        ("noncontrolling interests", "minority interests"),
    ),
    MetricPattern("preferred_stock", "Preferred stock", ("preferred stock",)),
    MetricPattern(
        "employee_options_value",
        "Employee options value",
        ("employee options value", "employee stock options value"),
    ),
)


def _currency_from_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    match = re.match(r"\s*([A-Z]{3})\b", unit.upper())
    return match.group(1) if match else None


def _reviewed_reporting_currency(candidates: list[FinancialExtractionCandidate]) -> ReportingCurrencyResolution:
    unit_currencies = {
        currency
        for candidate in candidates
        for currency in [_currency_from_unit(candidate.unit)]
        if currency is not None
    }
    metadata_currencies: set[str] = set()
    for candidate in candidates:
        payload = candidate.raw_document.raw_payload_json or {}
        for key in ("reporting_currency", "currency"):
            value = payload.get(key)
            if isinstance(value, str) and re.fullmatch(r"[A-Za-z]{3}", value.strip()):
                metadata_currencies.add(value.strip().upper())
    currencies = unit_currencies | metadata_currencies
    if len(currencies) > 1:
        raise HTTPException(
            status_code=422,
            detail=f"Reviewed financial candidates contain conflicting currencies: {', '.join(sorted(currencies))}",
        )
    currency = next(iter(currencies), None)
    if currency is None:
        return ReportingCurrencyResolution(None, None, "low")
    if unit_currencies:
        return ReportingCurrencyResolution(currency, "reviewed_candidate_unit", "high")
    return ReportingCurrencyResolution(currency, "filing_metadata", "medium")


def _reviewed_period_end(candidates: list[FinancialExtractionCandidate]) -> date | None:
    period_ends: set[date] = set()
    for candidate in candidates:
        raw_end = (candidate.source_locator_json or {}).get("end")
        if not isinstance(raw_end, str):
            continue
        try:
            period_ends.add(date.fromisoformat(raw_end))
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Reviewed financial candidate {candidate.id} has an invalid period-end date",
            ) from exc
    if len(period_ends) > 1:
        raise HTTPException(
            status_code=422,
            detail="Reviewed financial candidates contain conflicting period-end dates",
        )
    return next(iter(period_ends), None)


def extract_financial_candidates_from_filing(db: Session, filing_id: int) -> FinancialExtractionResultRead:
    document = db.get(RawDocument, filing_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Filing not found")
    if document.company_id is None:
        raise HTTPException(status_code=422, detail="Filing must be linked to a company before financial extraction")
    if not document.raw_text or not document.raw_text.strip():
        raise HTTPException(status_code=422, detail="Filing raw_text is required before financial extraction")

    existing_keys = {
        tuple(row)
        for row in db.execute(
            select(
                FinancialExtractionCandidate.metric_code,
                FinancialExtractionCandidate.fiscal_year,
                FinancialExtractionCandidate.period_type,
            ).where(
                FinancialExtractionCandidate.raw_document_id == document.id,
                FinancialExtractionCandidate.extraction_method == EXTRACTION_METHOD,
            )
        ).all()
    }

    extracted = _extract_candidates(document)
    created: list[FinancialExtractionCandidate] = []
    skipped_existing_count = 0
    for candidate in extracted:
        candidate_key = (candidate.metric_code, candidate.fiscal_year, candidate.period_type)
        if candidate_key in existing_keys:
            skipped_existing_count += 1
            continue
        db.add(candidate)
        created.append(candidate)

    _mark_setup_financial_extraction_needs_review(db, document.company_id)
    db.commit()
    for candidate in created:
        db.refresh(candidate)

    return FinancialExtractionResultRead(
        raw_document_id=document.id,
        created_count=len(created),
        skipped_existing_count=skipped_existing_count,
        candidates=created,
    )


def list_extracted_financial_candidates(db: Session, company_id: int) -> list[FinancialExtractionCandidate]:
    return list(
        db.scalars(
            select(FinancialExtractionCandidate)
            .where(FinancialExtractionCandidate.company_id == company_id)
            .where(FinancialExtractionCandidate.review_status != "promoted")
            .order_by(
                FinancialExtractionCandidate.fiscal_year.desc().nullslast(),
                FinancialExtractionCandidate.raw_document_id.desc(),
                FinancialExtractionCandidate.id,
            )
        )
    )


def _review_candidate(db: Session, candidate_id: int, expected_updated_at: datetime | None) -> FinancialExtractionCandidate:
    candidate = db.scalar(select(FinancialExtractionCandidate).where(FinancialExtractionCandidate.id == candidate_id)
                          .with_for_update().execution_options(populate_existing=True))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.review_status == "promoted":
        raise HTTPException(status_code=409, detail="Candidate was already promoted. Reload candidates before continuing.")
    if expected_updated_at is not None and _utc(candidate.updated_at) != _utc(expected_updated_at):
        raise HTTPException(status_code=409, detail="Candidate changed since it was loaded. Reload candidates and review the current evidence before saving.")
    return candidate


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def update_candidate_review_status(db: Session, candidate_id: int, status: str,
                                  expected_updated_at: datetime | None = None) -> FinancialExtractionCandidate:
    candidate = _review_candidate(db, candidate_id, expected_updated_at)
    if status == "reviewed" and not (candidate.unit and candidate.unit.strip()):
        raise HTTPException(
            status_code=422,
            detail="A reporting unit is required before a financial candidate can be reviewed",
        )
    candidate.review_status = status
    db.commit()
    db.refresh(candidate)
    return candidate


def override_candidate_value(db: Session, candidate_id: int, value: float, unit: str | None,
                             expected_updated_at: datetime | None = None) -> FinancialExtractionCandidate:
    candidate = _review_candidate(db, candidate_id, expected_updated_at)
    effective_unit = unit.strip() if unit and unit.strip() else candidate.unit
    if not effective_unit:
        raise HTTPException(
            status_code=422,
            detail="A reporting unit is required before a financial candidate can be overridden",
        )
    candidate.value = value
    candidate.unit = effective_unit
    candidate.review_status = "overridden"
    db.commit()
    db.refresh(candidate)
    return candidate


def promote_reviewed_candidates(db: Session, company_id: int, expected_candidates: list | None = None) -> int:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    candidates = db.scalars(
        select(FinancialExtractionCandidate)
        .where(FinancialExtractionCandidate.company_id == company_id)
        .where(FinancialExtractionCandidate.review_status.in_(["reviewed", "overridden"]))
        .order_by(FinancialExtractionCandidate.id)
        .with_for_update().execution_options(populate_existing=True)
    ).all()

    if expected_candidates is not None:
        expected = {item.id: _utc(item.updated_at) for item in expected_candidates}
        actual = {item.id: _utc(item.updated_at) for item in candidates}
        if len(expected) != len(expected_candidates) or actual != expected:
            raise HTTPException(status_code=409, detail="Reviewed candidates changed. Reload candidates and inspect the current values before promotion. No financial values were written.")

    if not candidates:
        return 0

    promoted_count = 0
    # Group by fiscal_year and period_type
    groups = {}
    for c in candidates:
        if c.fiscal_year is None:
            continue
        key = (c.fiscal_year, c.period_type)
        if key not in groups:
            groups[key] = []
        groups[key].append(c)

    reporting_currencies = {
        key: _reviewed_reporting_currency(group_candidates)
        for key, group_candidates in groups.items()
    }
    report_dates = {
        key: _reviewed_period_end(group_candidates)
        for key, group_candidates in groups.items()
    }
    # A statement and its notes can repeat the same fact. Preserve both source
    # revisions, but never silently choose between conflicting reviewed values.
    for group_candidates in groups.values():
        values_by_code = {}
        for candidate in group_candidates:
            value = (candidate.value, candidate.unit)
            previous = values_by_code.setdefault(candidate.metric_code, value)
            if previous != value:
                raise HTTPException(status_code=409, detail="Reviewed candidates contain conflicting values or units for the same period and metric. Resolve the source selection before promotion. No financial values were written.")

    for (year, period_type), group_candidates in groups.items():
        currency_resolution = reporting_currencies[(year, period_type)]
        exact_report_date = report_dates[(year, period_type)]
        reporting_currency = currency_resolution.currency or company.currency or "USD"
        currency_source = currency_resolution.source or ("company_fallback" if company.currency else "system_default")
        currency_confidence = currency_resolution.confidence if currency_resolution.currency else "low"
        # Find or create period
        period = db.scalar(
            select(FinancialStatementPeriod)
            .where(FinancialStatementPeriod.company_id == company_id)
            .where(FinancialStatementPeriod.year == year)
            .where(FinancialStatementPeriod.period_type == period_type)
        )
        if not period:
            period = FinancialStatementPeriod(
                company_id=company_id,
                period_type=period_type,
                year=year,
                report_date=exact_report_date or date(year, 12, 31),
                currency=reporting_currency,
                currency_source=currency_source,
                currency_confidence=currency_confidence,
            )
            db.add(period)
            db.flush()
        elif currency_resolution.currency is not None or period.currency_source in {"legacy_unknown", "company_fallback", "system_default"}:
            period.currency = reporting_currency
            period.currency_source = currency_source
            period.currency_confidence = currency_confidence
        if exact_report_date is not None:
            period.report_date = exact_report_date

        # Reuse pending inserts as well as stored rows. Sessions disable
        # autoflush, so a database query alone cannot see the first occurrence.
        period_metrics = db.scalars(select(FinancialMetric).where(FinancialMetric.period_id == period.id)).all()
        metrics_by_code = {metric.metric_name: metric for metric in period_metrics}
        if len(metrics_by_code) != len(period_metrics):
            raise HTTPException(status_code=409, detail="The financial period contains duplicate stored metrics. Reconcile those records before promotion.")
        for candidate in group_candidates:
            metric = metrics_by_code.get(candidate.metric_code)
            if metric:
                metric.value = candidate.value
                metric.unit = candidate.unit
            else:
                metric = FinancialMetric(
                    period_id=period.id,
                    metric_name=candidate.metric_code,
                    value=candidate.value,
                    unit=candidate.unit
                )
                db.add(metric)
                metrics_by_code[candidate.metric_code] = metric

            record_financial_fact_revision(
                db,
                candidate,
                effective_at=period.report_date,
            )
            # The next repeated occurrence must see this revision when assigning
            # its sequence and superseding the prior occurrence in this transaction.
            db.flush()

            # Delete the candidate after promotion or mark as promoted
            candidate.review_status = "promoted"
            promoted_count += 1

        db.flush()
        MetricNormalizationEngine.normalize_period(db, period.id, commit=False)

    db.commit()
    return promoted_count


def preview_financial_candidates(document: RawDocument) -> list[FinancialExtractionCandidate]:
    """Run the text extractor without persisting or promoting its candidates."""
    return _extract_candidates(document)


def _extract_candidates(document: RawDocument) -> list[FinancialExtractionCandidate]:
    assert document.raw_text is not None
    candidates: list[FinancialExtractionCandidate] = []
    matched_keys: set[tuple[str, int | None, str]] = set()
    default_fiscal_year = _guess_fiscal_year(document)
    period_type = "annual" if document.document_type == "annual_report" else "unknown"
    for source_line in _source_lines(document.raw_text):
        line = source_line.text
        lowered = line.lower()
        for pattern in METRIC_PATTERNS:
            match = _find_alias_match(lowered, pattern.aliases)
            if match is None:
                continue
            fiscal_year = _line_fiscal_year(line, match, default_fiscal_year)
            candidate_key = (pattern.metric_code, fiscal_year, period_type)
            if candidate_key in matched_keys:
                continue
            value = _extract_metric_value(line, match, fiscal_year)
            if value is None:
                continue
            matched_keys.add(candidate_key)
            warnings = ["reporting_unit_missing"]
            if _line_fiscal_year(line, match, None) is None and fiscal_year is not None:
                warnings.append("fiscal_year_inferred_from_document")
            if _numeric_value_count(line, match, fiscal_year) > 1:
                warnings.append("multiple_numeric_values_on_source_line")
            candidates.append(
                FinancialExtractionCandidate(
                    company_id=document.company_id,
                    raw_document_id=document.id,
                    metric_code=pattern.metric_code,
                    reported_label=pattern.reported_label,
                    value=value,
                    unit=None,
                    fiscal_year=fiscal_year,
                    period_type=period_type,
                    source_text=line,
                    source_line_number=source_line.line_number,
                    source_page=source_line.page,
                    source_section=source_line.section,
                    source_locator_json={
                        "type": "text_line",
                        "line_number": source_line.line_number,
                        "page": source_line.page,
                        "section": source_line.section,
                    },
                    extraction_warnings=";".join(warnings),
                    extraction_method=EXTRACTION_METHOD,
                    confidence_label="low" if warnings else "medium",
                    review_status="needs_review",
                )
            )
            break
    return candidates


def _source_lines(raw_text: str) -> list[SourceLine]:
    lines: list[SourceLine] = []
    page: int | None = None
    section: str | None = None
    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        if "\f" in raw_line:
            page = (page or 0) + raw_line.count("\f")
        text = raw_line.replace("\f", " ").strip()
        if not text:
            continue
        page_match = re.fullmatch(r"\[?\s*page\s+(\d+)\s*\]?", text, re.IGNORECASE)
        if page_match:
            page = int(page_match.group(1))
            continue
        if _is_section_heading(text):
            section = text[:255]
            continue
        lines.append(SourceLine(line_number=line_number, text=text, page=page, section=section))
    return lines


def _is_section_heading(text: str) -> bool:
    return bool(
        re.match(r"^ITEM\s+\d+[A-Z]?[.]?\s+", text, re.IGNORECASE)
        or re.match(r"^(?:CONSOLIDATED\s+)?(?:STATEMENTS?|BALANCE\s+SHEETS?)\b", text, re.IGNORECASE)
    )


def _find_alias_match(line: str, aliases: tuple[str, ...]) -> re.Match[str] | None:
    for alias in aliases:
        match = re.search(rf"\b{re.escape(alias)}\b", line)
        if match is not None:
            return match
    return None


def _extract_number(text: str) -> float | None:
    match = re.search(r"\(?[-+]?\d[\d,]*(?:\.\d+)?\)?", text)
    if match is None:
        return None
    raw = match.group(0)
    negative = raw.startswith("(") and raw.endswith(")")
    cleaned = raw.strip("()").replace(",", "")
    value = float(cleaned)
    return -value if negative else value


def _line_fiscal_year(line: str, alias_match: re.Match[str], default: int | None) -> int | None:
    explicit_patterns = (
        r"\bFY\s*[-:]?\s*(19\d{2}|20\d{2})\b",
        r"\bfiscal\s+year(?:\s+ended)?\s+(19\d{2}|20\d{2})\b",
        r"\byear\s+ended\s+(19\d{2}|20\d{2})\b",
    )
    for pattern in explicit_patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return int(match.group(1))

    prefix_years = re.findall(r"\b(19\d{2}|20\d{2})\b", line[:alias_match.start()])
    if prefix_years:
        return int(prefix_years[-1])

    suffix = line[alias_match.end():]
    suffix_year = re.match(r"\s*[\[(]?\s*(19\d{2}|20\d{2})\s*[\])]?(?:\s*[:|-])", suffix)
    return int(suffix_year.group(1)) if suffix_year else default


def _extract_metric_value(line: str, alias_match: re.Match[str], fiscal_year: int | None) -> float | None:
    suffix = line[alias_match.end():]
    suffix = re.sub(r"\bFY\s*[-:]?\s*(?:19\d{2}|20\d{2})\b", " ", suffix, flags=re.IGNORECASE)
    if fiscal_year is not None:
        suffix = re.sub(rf"\b{fiscal_year}\b\s*[:|-]?", " ", suffix, count=1)
    value = _extract_number(suffix)
    return value if value is not None else _extract_number(line)


def _numeric_value_count(line: str, alias_match: re.Match[str], fiscal_year: int | None) -> int:
    suffix = line[alias_match.end():]
    suffix = re.sub(r"\bFY\s*[-:]?\s*(?:19\d{2}|20\d{2})\b", " ", suffix, flags=re.IGNORECASE)
    if fiscal_year is not None:
        suffix = re.sub(rf"\b{fiscal_year}\b\s*[:|-]?", " ", suffix, count=1)
    return len(re.findall(r"\(?[-+]?\d[\d,]*(?:\.\d+)?\)?", suffix))


def _guess_fiscal_year(document: RawDocument) -> int | None:
    payload = document.raw_payload_json or {}
    payload_year = payload.get("fiscal_year")
    if isinstance(payload_year, int) and 1900 <= payload_year <= 2100:
        return payload_year
    match = re.search(r"\b(20\d{2}|19\d{2})\b", document.title or "")
    if match:
        return int(match.group(1))
    return document.published_at.year if document.published_at is not None else None


def _mark_setup_financial_extraction_needs_review(db: Session, company_id: int) -> None:
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        return
    workflow.financial_extraction_status = "needs_review"
    workflow.current_step = "financial_review"
