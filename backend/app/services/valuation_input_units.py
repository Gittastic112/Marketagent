"""Convert explicit reporting scales for draft inputs without changing source facts."""
import math


INPUT_UNIT_POLICY = "full_currency_and_shares_v1"
MONEY_FIELDS = {
    "revenue", "starting_revenue", "ebit", "cash", "debt", "invested_capital",
    "starting_invested_capital", "operating_leases", "lease_liabilities",
    "cross_holdings", "minority_interests", "preferred_stock", "employee_options_value",
    "net_income", "capex", "depreciation", "change_in_nwc", "new_debt_issued",
    "debt_repaid", "dividends", "buybacks", "stock_issuances", "book_equity",
    "book_value_of_equity", "distress_sale_proceeds",
}
SHARE_FIELDS = {"diluted_shares", "basic_shares"}
SCALES = {"thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000,
          "lakh": 100_000, "crore": 10_000_000}


def canonical_financial_input(field, value, source, currency):
    if field not in MONEY_FIELDS | SHARE_FIELDS:
        return value, source
    source = dict(source)
    tokens = str(source.get("unit") or "").casefold().split()
    dimension = "shares" if field in SHARE_FIELDS else (currency or "").upper()
    marker = "shares" if field in SHARE_FIELDS else (currency or "").casefold()
    if field in SHARE_FIELDS:
        tokens = ["shares" if token == "share" else token for token in tokens]
    factor = None
    if marker and tokens.count(marker) == 1:
        tokens.remove(marker)
        if not tokens:
            factor = 1
        elif len(tokens) == 1:
            factor = SCALES.get(tokens[0].removesuffix("s"))
    source.update(original_value=value, input_unit=dimension,
        unit_multiplier=factor, input_unit_policy=INPUT_UNIT_POLICY)
    if factor is None or not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value * factor):
        warning = "This source unit cannot be aligned with the draft currency or share count. The suggested value is unavailable; enter an explicitly reviewed value in full currency units or full shares."
        source.update(unit_alignment_status="unavailable", requires_review=True,
            warnings=" ".join(filter(None, [source.get("warnings"), warning])))
        return None, source
    source["unit_alignment_status"] = "converted" if factor != 1 else "aligned"
    if factor != 1:
        source.update(claim_type="Calculation", label=source.get("label", "Reported input") + " (unit conversion)",
            unit_conversion_formula=f"Reported value × {factor:,} = full {dimension}")
    return value * factor, source
