"""Source period identity, retained without guessing dates or rewriting old rows."""
from datetime import date


def _date(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def financial_period_basis(candidate, *, effective_at=None):
    locator = candidate.source_locator_json or {}
    saved = locator.get("promoted_period_basis")
    if isinstance(saved, dict) and saved.get("version") == "financial-period-v1":
        return dict(saved)
    review = locator.get("period_review") or {}
    start = _date(locator.get("start"))
    end = _date(locator.get("end")) or _date(review.get("end"))
    instant = _date(locator.get("instant"))
    # Missing start alone never proves an instant: legacy extraction often omitted it.
    scope = "instant" if instant else candidate.period_type
    basis = locator.get("accounting_basis") or locator.get("taxonomy")
    basis = basis if isinstance(basis, str) and basis.strip() else None
    return {
        "version": "financial-period-v1", "fiscal_year": candidate.fiscal_year,
        "scope": scope, "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
        "instant": instant.isoformat() if instant else None,
        "duration_days": (end - start).days + 1 if start and end else None,
        "accounting_basis": basis,
        "end_basis": "source" if _date(locator.get("end")) else "User Assumption" if end else "unknown",
        "stored_effective_at": effective_at.isoformat() if effective_at else None,
        "identity_status": "source_dated" if end or instant else "legacy_date_only" if effective_at else "unresolved",
    }


def period_scope_key(basis):
    return tuple(basis.get(key) for key in ("scope", "start", "end", "instant", "accounting_basis"))
