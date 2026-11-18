"""Map actual EdgarTools fact objects without its remote company/client layer."""
from datetime import date
import math


def parse_company_facts(payload: dict, *, as_of: str, currency: str, max_years: int = 5) -> dict:
    from edgar.entity.parser import EntityFactsParser
    from app.services.sec_xbrl_extractor import FLOW_METRICS, US_GAAP_MAPPING, CONCEPT_PRIORITY, CORE_METRICS

    cutoff = date.fromisoformat(as_of)
    entity = EntityFactsParser.parse_company_facts(payload)
    if entity is None:
        raise ValueError("No parseable company facts")
    selected, excluded = {}, 0
    for fact in entity:
        concept = fact.concept.removeprefix("us-gaap:")
        metric = US_GAAP_MAPPING.get(concept)
        if fact.taxonomy != "us-gaap" or metric is None:
            continue
        expected_unit = "shares" if metric in {"basic_shares", "diluted_shares"} else currency
        if (fact.unit != expected_unit or fact.form_type not in {"10-K", "10-K/A"}
                or fact.fiscal_period not in {"FY", ""} or not fact.period_end or not fact.filing_date
                or fact.period_end > cutoff or fact.filing_date > cutoff or not fact.accession
                or isinstance(fact.value, bool) or fact.numeric_value is None or not math.isfinite(fact.numeric_value)
                or (metric in FLOW_METRICS and (not fact.period_start or not 300 <= (fact.period_end - fact.period_start).days <= 380))):
            excluded += 1
            continue
        key = (metric, fact.period_end.year)
        quality = (fact.filing_date, -CONCEPT_PRIORITY[metric][concept], fact.accession)
        if key not in selected or quality > selected[key][0]:
            selected[key] = (quality, {"metric_code": metric, "reported_label": fact.label,
                "value": fact.numeric_value, "unit": fact.unit, "fiscal_year": fact.period_end.year,
                "period_type": "annual", "source_text": f"XBRL {fact.taxonomy}:{concept}",
                "source_row_label": fact.label, "source_column_label": str(fact.period_end),
                "source_locator_json": {"type": "xbrl_fact", "namespace": fact.taxonomy,
                    "taxonomy": fact.taxonomy, "concept": concept, "start": fact.period_start.isoformat() if fact.period_start else None,
                    "end": fact.period_end.isoformat(), "instant": fact.period_end.isoformat() if not fact.period_start else None,
                    "filed": fact.filing_date.isoformat(), "accession": fact.accession,
                    "form": fact.form_type, "fp": fact.fiscal_period, "reported_fy": fact.fiscal_year,
                    "as_of": as_of, "selection_policy": "latest_eligible_filing_then_concept_priority",
                    "publication_precision": "date", "unit": fact.unit},
                "confidence_label": "high", "extraction_warnings": "Date-only filing availability; not suitable for intraday knowledge claims."})
    years = sorted({key[1] for key in selected}, reverse=True)[:max_years]
    missing = {str(year): sorted(CORE_METRICS - {metric for metric, year_key in selected if year_key == year}) for year in years}
    return {"candidates": [value[1] for key, value in sorted(selected.items()) if key[1] in years],
        "excluded_count": excluded, "fetched_count": len(entity), "fiscal_years": sorted(years),
        "missing_core_metrics_by_year": missing,
        "warnings": ["ANNUAL_CANDIDATES_REQUIRE_REVIEW", "FILING_AVAILABILITY_HAS_DATE_PRECISION",
                     *(["NO_ELIGIBLE_ANNUAL_FACTS"] if not years else []),
                     *(["CORE_METRIC_COVERAGE_INCOMPLETE"] if any(missing.values()) else [])]}
