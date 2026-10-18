import math
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.services.financial_metric_derivations import derive_reported_metrics
from app.models.financial import (
    FinancialStatementPeriod,
    FinancialMetric,
    NormalizedFinancialSnapshot,
    NormalizedFinancialMetric,
)

class RDCapitalizationService:
    @staticmethod
    def calculate_capitalized_rd(current_rd: float, historical_rd: List[float]) -> Dict[str, float]:
        """
        Calculates R&D Asset and Amortization according to Damodaran's formula.
        historical_rd must contain up to 5 years of historical R&D expense.
        Index 0 is 1 year ago, Index 1 is 2 years ago, etc.
        """
        # Ensure we have 5 years of history to calculate the asset, pad with 0 if necessary
        padded_history = historical_rd + [0.0] * (5 - len(historical_rd))

        rd_1y = padded_history[0]
        rd_2y = padded_history[1]
        rd_3y = padded_history[2]
        rd_4y = padded_history[3]
        rd_5y = padded_history[4]

        # R&D Asset = Current R&D + 80%*1Y + 60%*2Y + 40%*3Y + 20%*4Y
        rd_asset = current_rd + (0.8 * rd_1y) + (0.6 * rd_2y) + (0.4 * rd_3y) + (0.2 * rd_4y)

        # R&D Amortization = (1Y + 2Y + 3Y + 4Y + 5Y) / 5
        rd_amortization = (rd_1y + rd_2y + rd_3y + rd_4y + rd_5y) / 5.0

        return {
            "rd_asset": rd_asset,
            "rd_amortization": rd_amortization
        }

    @staticmethod
    def calculate_adjusted_metrics(reported_ebit: float, reported_invested_capital: float, current_rd: float, rd_asset: float, rd_amortization: float) -> Dict[str, float]:
        adjusted_ebit = reported_ebit + current_rd - rd_amortization
        adjusted_ic = reported_invested_capital + rd_asset
        adjusted_roc = adjusted_ebit / adjusted_ic if adjusted_ic != 0 else 0

        return {
            "adjusted_ebit": adjusted_ebit,
            "adjusted_invested_capital": adjusted_ic,
            "adjusted_roc": adjusted_roc
        }

class GoodwillDiagnosticsService:
    @staticmethod
    def diagnose(goodwill: float, total_assets: float, impairment_expense: float = 0.0) -> Dict[str, Any]:
        """
        Evaluates goodwill to flag acquisition intensity.
        """
        ratio = goodwill / total_assets if total_assets != 0 else 0

        warnings = []
        if ratio > 0.2:
            warnings.append("High Acquisition Intensity: Goodwill > 20% of total assets. Organic growth assumptions may be flawed.")
        if impairment_expense > 0:
             warnings.append(f"Recent Impairment: ${impairment_expense} in goodwill impairment suggests past overpayment.")

        return {
            "goodwill_to_assets": ratio,
            "warnings": warnings,
            "acquisition_heavy": ratio > 0.2
        }

class AccountingNormalizationService:
    @staticmethod
    def normalize_rd(reported_ebit: float, reported_ic: float, current_rd: float, historical_rd: List[float]) -> Dict[str, Any]:
        rd_calc = RDCapitalizationService.calculate_capitalized_rd(current_rd, historical_rd)
        metrics = RDCapitalizationService.calculate_adjusted_metrics(
            reported_ebit,
            reported_ic,
            current_rd,
            rd_calc["rd_asset"],
            rd_calc["rd_amortization"]
        )
        return {**rd_calc, **metrics}

class MetricNormalizationEngine:
    @staticmethod
    def _get_metric_value(metrics: List[FinancialMetric], codes: List[str]) -> Optional[float]:
        for code in codes:
            for m in metrics:
                if m.metric_name == code:
                    return m.value
        return None

    @staticmethod
    def normalize_period(db: Session, period_id: int, *, commit: bool = True) -> NormalizedFinancialSnapshot:
        period = db.get(FinancialStatementPeriod, period_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")

        metrics = list(period.metrics)

        # We will clear existing snapshots for this period
        existing_snapshots = db.scalars(select(NormalizedFinancialSnapshot).where(NormalizedFinancialSnapshot.period_id == period_id)).all()
        for snap in existing_snapshots:
            db.delete(snap)

        snapshot = NormalizedFinancialSnapshot(
            company_id=period.company_id,
            period_id=period_id
        )
        db.add(snapshot)
        db.flush()
        db.refresh(snapshot)

        from app.models.financial import FinancialExtractionCandidate
        candidates = db.scalars(
            select(FinancialExtractionCandidate)
            .where(FinancialExtractionCandidate.company_id == period.company_id)
            .where(FinancialExtractionCandidate.fiscal_year == period.year)
            .where(FinancialExtractionCandidate.period_type == period.period_type)
            .where(FinancialExtractionCandidate.review_status.in_(["promoted", "overridden", "reviewed"]))
        ).all()
        candidate_map = {c.metric_code: c for c in candidates}
        currency_context = (
            f"Reporting currency: {period.currency} "
            f"({period.currency_source}, {period.currency_confidence} confidence)"
        )

        def build_provenance(codes: List[str], base_note: str) -> str:
            sources = []
            for code in codes:
                if code in candidate_map:
                    cand = candidate_map[code]
                    source = f"{code}: {cand.extraction_method}"
                    if cand.source_text:
                        # Truncate source_text if too long
                        stext = cand.source_text if len(cand.source_text) <= 50 else cand.source_text[:47] + "..."
                        source += f" ('{stext}')"
                    sources.append(source)
            if sources:
                base_note += " | Sources: " + ", ".join(sources)
            return f"{base_note} | {currency_context}"

        def add_metric(
            code: str,
            v: float,
            notes: str = "",
            warns: str = "",
            source_codes: List[str] = None,
            unit: str | None = None,
        ):
            if source_codes:
                notes = build_provenance(source_codes, notes)
            nm = NormalizedFinancialMetric(
                snapshot_id=snapshot.id,
                metric_code=code,
                value=v,
                unit=unit,
                provenance_notes=notes,
                warnings=warns if warns else None
            )
            db.add(nm)

        reported = {}
        for metric in metrics:
            reported.setdefault(metric.metric_name, (metric.value, metric.unit))
        for code, item in derive_reported_metrics(reported).items():
            add_metric(code, item.value, item.notes, item.warnings,
                       list(item.source_codes), item.unit)

        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(snapshot)
        return snapshot


class NormalizedSnapshotBackfillService:
    BRIDGE_ALIASES = {
        "cash": {"cash", "cash_and_equivalents"},
        "debt": {"debt", "total_debt", "short_term_debt", "long_term_debt"},
        "diluted_shares": {"diluted_shares", "weighted_average_diluted_shares"},
        "capex": {"capital_expenditures", "capex"},
        "depreciation": {"depreciation_and_amortization", "da", "depreciation"},
        "change_in_nwc": {"change_in_working_capital", "nwc_change", "change_in_nwc"},
        "acquisitions": {"acquisitions", "business_acquisitions"},
        "basic_shares": {"basic_shares", "weighted_average_basic_shares"},
        "operating_leases": {"operating_leases", "lease_liabilities", "operating_lease_liabilities"},
        "minority_interests": {"minority_interests", "noncontrolling_interests"},
        "preferred_stock": {"preferred_stock"},
        "employee_options_value": {"employee_options_value"},
        "cross_holdings": {"cross_holdings", "cross_holdings_value"},
    }

    @staticmethod
    def _naive(value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=None) if value is not None else None

    @staticmethod
    def _currency_resolution(period: FinancialStatementPeriod) -> tuple[str, str, str]:
        currencies = {
            match.group(1)
            for metric in period.metrics
            for match in [re.match(r"\s*([A-Z]{3})\b", (metric.unit or "").upper())]
            if match is not None
        }
        if len(currencies) > 1:
            raise ValueError(
                f"Period {period.id} contains conflicting metric currencies: {', '.join(sorted(currencies))}"
            )
        if currencies:
            return next(iter(currencies)), "financial_metric_unit_backfill", "medium"
        if period.company.currency:
            return period.company.currency, "company_fallback", "low"
        return period.currency or "USD", "system_default", "low"

    @staticmethod
    def _inspect_period(db: Session, period: FinancialStatementPeriod) -> dict[str, Any]:
        snapshot = db.scalar(
            select(NormalizedFinancialSnapshot)
            .where(NormalizedFinancialSnapshot.period_id == period.id)
            .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
        )
        reasons: list[str] = []
        if snapshot is None:
            reasons.append("missing_snapshot")
            normalized_codes: set[str] = set()
        else:
            normalized_codes = {
                metric.metric_code
                for metric in db.scalars(
                    select(NormalizedFinancialMetric).where(NormalizedFinancialMetric.snapshot_id == snapshot.id)
                )
            }
            source_updated_at = max(
                (
                    NormalizedSnapshotBackfillService._naive(metric.updated_at)
                    for metric in period.metrics
                    if metric.updated_at is not None
                ),
                default=None,
            )
            if (
                source_updated_at
                and snapshot.updated_at
                and source_updated_at > NormalizedSnapshotBackfillService._naive(snapshot.updated_at)
            ):
                reasons.append("source_metrics_updated")

        source_codes = {metric.metric_name for metric in period.metrics}
        missing_bridge = sorted(
            target
            for target, aliases in NormalizedSnapshotBackfillService.BRIDGE_ALIASES.items()
            if source_codes.intersection(aliases) and target not in normalized_codes
        )
        if missing_bridge:
            reasons.append("missing_bridge_metrics:" + ",".join(missing_bridge))
        if period.currency_source == "legacy_unknown":
            reasons.append("legacy_currency_provenance")

        currency_conflict: str | None = None
        try:
            currency, currency_source, currency_confidence = NormalizedSnapshotBackfillService._currency_resolution(period)
        except ValueError as exc:
            currency_conflict = str(exc)
            reasons.append("currency_conflict")
            currency = period.currency
            currency_source = period.currency_source
            currency_confidence = period.currency_confidence

        needs_backfill = bool(reasons)
        trust_ready = (
            snapshot is not None
            and bool(normalized_codes)
            and not needs_backfill
            and period.currency_confidence in {"medium", "high"}
        )
        return {
            "period_id": period.id,
            "year": period.year,
            "quarter": period.quarter,
            "period_type": period.period_type,
            "source_metric_count": len(period.metrics),
            "normalized_metric_count": len(normalized_codes),
            "needs_backfill": needs_backfill,
            "trust_ready": trust_ready,
            "reasons": reasons,
            "currency": currency,
            "currency_source": currency_source,
            "currency_confidence": currency_confidence,
            "currency_conflict": currency_conflict,
        }

    @staticmethod
    def summarize(db: Session, company_id: int) -> dict[str, Any]:
        periods = list(
            db.scalars(
                select(FinancialStatementPeriod)
                .where(FinancialStatementPeriod.company_id == company_id)
                .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
            )
        )
        details = [NormalizedSnapshotBackfillService._inspect_period(db, period) for period in periods]
        period_count = len(details)
        normalized_count = sum(item["normalized_metric_count"] > 0 for item in details)
        needs_backfill_count = sum(item["needs_backfill"] for item in details)
        conflict_count = sum(item["currency_conflict"] is not None for item in details)
        trust_ready_count = sum(item["trust_ready"] for item in details)
        coverage_percent = round((normalized_count / period_count) * 100, 1) if period_count else 0.0

        if not details:
            status = "no_data"
        elif conflict_count:
            status = "blocked"
        elif needs_backfill_count:
            status = "partial"
        else:
            status = "complete"

        actions: list[str] = []
        if conflict_count:
            actions.append("Resolve conflicting metric currencies before normalization.")
        if needs_backfill_count > conflict_count:
            actions.append("Preview and apply the normalized snapshot backfill.")
        if details and trust_ready_count < period_count:
            actions.append("Review low-confidence reporting currencies before valuation use.")

        return {
            "status": status,
            "period_count": period_count,
            "normalized_period_count": normalized_count,
            "coverage_percent": coverage_percent,
            "trust_ready_period_count": trust_ready_count,
            "needs_backfill_count": needs_backfill_count,
            "conflict_count": conflict_count,
            "low_confidence_currency_count": sum(
                item["currency_confidence"] not in {"medium", "high"} for item in details
            ),
            "stale_snapshot_count": sum(
                "source_metrics_updated" in item["reasons"] for item in details
            ),
            "missing_snapshot_count": sum("missing_snapshot" in item["reasons"] for item in details),
            "periods": details,
            "recommended_actions": actions,
        }

    @staticmethod
    def backfill(db: Session, company_id: int, *, dry_run: bool = True) -> Dict[str, Any]:
        periods = list(
            db.scalars(
                select(FinancialStatementPeriod)
                .where(FinancialStatementPeriod.company_id == company_id)
                .order_by(FinancialStatementPeriod.year, FinancialStatementPeriod.quarter)
            )
        )
        coverage_before = NormalizedSnapshotBackfillService.summarize(db, company_id)
        inspected = [NormalizedSnapshotBackfillService._inspect_period(db, period) for period in periods]
        skipped_conflicts = [
            {"period_id": item["period_id"], "error": item["currency_conflict"]}
            for item in inspected
            if item["currency_conflict"] is not None
        ]
        eligible = [
            item for item in inspected if item["needs_backfill"] and item["currency_conflict"] is None
        ]

        if not dry_run:
            for item in eligible:
                period = db.get(FinancialStatementPeriod, item["period_id"])
                period.currency = item["currency"]
                period.currency_source = item["currency_source"]
                period.currency_confidence = item["currency_confidence"]
                MetricNormalizationEngine.normalize_period(db, period.id, commit=False)
            db.commit()

        coverage_after = None if dry_run else NormalizedSnapshotBackfillService.summarize(db, company_id)

        return {
            "dry_run": dry_run,
            "examined_count": len(periods),
            "eligible_count": len(eligible),
            "normalized_count": 0 if dry_run else len(eligible),
            "eligible_periods": eligible,
            "skipped_conflicts": skipped_conflicts,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
        }


class FinancialReconciliationService:
    CANONICAL_ALIASES: dict[str, tuple[str, ...]] = {
        "revenue": ("revenue", "total_revenue"),
        "ebit": ("ebit", "operating_income"),
        "ebitda": ("ebitda",),
        "net_income": ("net_income_parent", "net_income", "profit"),
        "cash": ("cash", "cash_and_equivalents"),
        "debt": ("debt", "total_debt", "short_term_debt", "long_term_debt"),
        "diluted_shares": ("diluted_shares", "weighted_average_diluted_shares"),
        "basic_shares": ("basic_shares", "weighted_average_basic_shares"),
        "capex": ("capital_expenditures", "capex"),
        "depreciation": ("depreciation_and_amortization", "da", "depreciation"),
        "change_in_nwc": ("change_in_working_capital", "nwc_change", "change_in_nwc"),
        "acquisitions": ("acquisitions", "business_acquisitions"),
        "operating_leases": ("operating_leases", "lease_liabilities", "operating_lease_liabilities"),
        "minority_interests": ("minority_interests", "noncontrolling_interests"),
        "preferred_stock": ("preferred_stock",),
        "employee_options_value": ("employee_options_value",),
        "cross_holdings": ("cross_holdings", "cross_holdings_value"),
    }

    @staticmethod
    def reconcile(db: Session, company_id: int) -> dict[str, Any]:
        periods = list(
            db.scalars(
                select(FinancialStatementPeriod)
                .where(FinancialStatementPeriod.company_id == company_id)
                .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
            )
        )
        period_reports = [FinancialReconciliationService._reconcile_period(db, period) for period in periods]
        items = [item for period in period_reports for item in period["items"]]
        counts = {
            status: sum(item["status"] == status for item in items)
            for status in ("exact", "mismatch", "missing_normalized", "normalized_only")
        }

        if not periods:
            status = "no_data"
        elif counts["mismatch"]:
            status = "blocked"
        elif counts["missing_normalized"] or counts["normalized_only"] or not items:
            status = "partial"
        else:
            status = "complete"

        actions: list[str] = []
        if counts["mismatch"]:
            actions.append("Re-run normalization or review changed source metrics before valuation use.")
        if counts["missing_normalized"]:
            actions.append("Backfill normalized snapshots for source metrics that are not represented.")
        if counts["normalized_only"]:
            actions.append("Review normalized-only values and confirm whether they are derived or stale.")

        return {
            "status": status,
            "period_count": len(periods),
            "item_count": len(items),
            "exact_count": counts["exact"],
            "mismatch_count": counts["mismatch"],
            "missing_normalized_count": counts["missing_normalized"],
            "normalized_only_count": counts["normalized_only"],
            "periods": period_reports,
            "recommended_actions": actions,
        }

    @staticmethod
    def _reconcile_period(db: Session, period: FinancialStatementPeriod) -> dict[str, Any]:
        snapshot = db.scalar(
            select(NormalizedFinancialSnapshot)
            .where(NormalizedFinancialSnapshot.period_id == period.id)
            .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
        )
        source_metrics = {metric.metric_name: metric for metric in period.metrics}
        normalized_metrics = (
            {
                metric.metric_code: metric
                for metric in db.scalars(
                    select(NormalizedFinancialMetric).where(
                        NormalizedFinancialMetric.snapshot_id == snapshot.id
                    )
                )
            }
            if snapshot is not None
            else {}
        )

        items: list[dict[str, Any]] = []
        for metric_code, aliases in FinancialReconciliationService.CANONICAL_ALIASES.items():
            source_metric = next((source_metrics[alias] for alias in aliases if alias in source_metrics), None)
            normalized_metric = normalized_metrics.get(metric_code)
            if (
                source_metric is None
                and normalized_metric is not None
                and (normalized_metric.provenance_notes or "").startswith("Computed:")
            ):
                continue
            if source_metric is None and normalized_metric is None:
                continue

            source_value = source_metric.value if source_metric is not None else None
            normalized_value = normalized_metric.value if normalized_metric is not None else None
            delta = (
                normalized_value - source_value
                if source_value is not None and normalized_value is not None
                else None
            )
            if source_metric is None:
                item_status = "normalized_only"
            elif normalized_metric is None:
                item_status = "missing_normalized"
            elif math.isclose(source_value, normalized_value, rel_tol=1e-9, abs_tol=1e-9):
                item_status = "exact"
            else:
                item_status = "mismatch"

            items.append(
                {
                    "metric_code": metric_code,
                    "source_metric_code": source_metric.metric_name if source_metric else None,
                    "status": item_status,
                    "source_value": source_value,
                    "normalized_value": normalized_value,
                    "delta": delta,
                    "delta_percent": (
                        delta / abs(source_value)
                        if delta is not None and source_value != 0
                        else None
                    ),
                    "source_unit": source_metric.unit if source_metric else None,
                    "normalized_unit": normalized_metric.unit if normalized_metric else None,
                    "provenance_notes": normalized_metric.provenance_notes if normalized_metric else None,
                    "warnings": normalized_metric.warnings if normalized_metric else None,
                }
            )

        mismatch_count = sum(item["status"] == "mismatch" for item in items)
        gap_count = sum(
            item["status"] in {"missing_normalized", "normalized_only"} for item in items
        )
        return {
            "period_id": period.id,
            "snapshot_id": snapshot.id if snapshot else None,
            "year": period.year,
            "quarter": period.quarter,
            "period_type": period.period_type,
            "status": "blocked" if mismatch_count else "partial" if gap_count or not items else "complete",
            "items": items,
        }
