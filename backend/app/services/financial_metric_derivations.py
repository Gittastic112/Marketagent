"""Normalize reported metrics without inventing missing calculation inputs.

Inputs and outputs contain no HTTP or persistence objects. Monetary arithmetic
requires matching reported units; currency conversion belongs to a separate flow.
"""
from dataclasses import dataclass
import math
from typing import Mapping


@dataclass(frozen=True)
class NormalizedMetric:
    value: float
    unit: str | None
    source_codes: tuple[str, ...]
    notes: str
    warnings: str | None = None


def derive_reported_metrics(
    metrics: Mapping[str, tuple[float, str | None]],
) -> dict[str, NormalizedMetric]:
    result: dict[str, NormalizedMetric] = {}

    def find(*codes: str) -> NormalizedMetric | None:
        for code in codes:
            if code in metrics:
                value, unit = metrics[code]
                if not math.isfinite(value):
                    return None
                return NormalizedMetric(value, unit, (code,), 'From reported line items')
        return None

    def matching_units(*values: NormalizedMetric | None) -> bool:
        return bool(values) and all(value is not None and value.unit for value in values) and len(
            {' '.join(value.unit.split()).casefold() for value in values}
        ) == 1

    def add(code: str, value: float, notes: str, *sources: NormalizedMetric,
            unit: str | None = None, warnings: str | None = None) -> NormalizedMetric | None:
        if not math.isfinite(value):
            return None
        item = NormalizedMetric(value, unit,
            tuple(dict.fromkeys(c for source in sources for c in source.source_codes)), notes, warnings)
        result[code] = item
        return item

    aliases = {
        'revenue': ('revenue', 'total_revenue'),
        'ebit': ('ebit', 'operating_income'),
        'ebitda': ('ebitda',),
        'net_income': ('net_income_parent', 'net_income', 'profit'),
        'cash': ('cash', 'cash_and_equivalents'),
        'debt': ('debt', 'total_debt'),
        'diluted_shares': ('diluted_shares', 'weighted_average_diluted_shares'),
        'basic_shares': ('basic_shares', 'weighted_average_basic_shares'),
        'capex': ('capital_expenditures', 'capex'),
        'depreciation': ('depreciation_and_amortization', 'da', 'depreciation'),
        'change_in_nwc': ('change_in_working_capital', 'nwc_change', 'change_in_nwc'),
        'acquisitions': ('acquisitions', 'business_acquisitions'),
        'lease_liabilities': ('operating_leases', 'lease_liabilities', 'operating_lease_liabilities'),
        'operating_leases': ('operating_leases', 'lease_liabilities', 'operating_lease_liabilities'),
        'minority_interests': ('minority_interests', 'noncontrolling_interests'),
        'preferred_stock': ('preferred_stock',),
        'employee_options_value': ('employee_options_value',),
        'cross_holdings': ('cross_holdings', 'cross_holdings_value'),
    }
    for code, names in aliases.items():
        item = find(*names)
        if item is not None:
            result[code] = item

    if 'debt' not in result:
        for names in (('current_debt', 'long_term_debt_noncurrent'),
                      ('short_term_borrowings', 'long_term_debt_total'),
                      ('short_term_debt', 'long_term_debt')):
            current, long_term = (find(name) for name in names)
            if matching_units(current, long_term):
                add('debt', current.value + long_term.value, 'Computed: ' + ' + '.join(names),
                    current, long_term, unit=current.unit,
                    warnings='Review lease inclusion and other financing claims.')
                break

    ebit, da = result.get('ebit'), result.get('depreciation')
    if 'ebitda' not in result and matching_units(ebit, da):
        add('ebitda', ebit.value + da.value, 'Computed: EBIT + D&A', ebit, da, unit=ebit.unit)

    tax, pretax = find('tax_expense', 'income_tax'), find('pre_tax_income', 'ebt')
    tax_rate = None
    # A historical effective rate needs a reported pre-tax denominator. EBIT is
    # not a replacement for pre-tax income when financing expenses are material.
    if matching_units(tax, pretax) and pretax.value > 0:
        rate = tax.value / pretax.value
        if 0 <= rate <= 1:
            tax_rate = add('effective_tax_rate', rate, 'Computed: Tax / Pre-Tax Income', tax, pretax)
    nopat = None
    if tax_rate is not None and matching_units(ebit, tax, pretax):
        nopat = add('nopat', ebit.value * (1 - tax_rate.value), 'Computed: EBIT * (1 - Tax Rate)',
                    ebit, tax_rate, unit=ebit.unit)

    debt, cash = result.get('debt'), result.get('cash')
    if matching_units(debt, cash):
        add('net_debt', debt.value - cash.value, 'Computed: Debt - Cash', debt, cash, unit=debt.unit)
    assets, liabilities = find('current_assets'), find('current_liabilities')
    if matching_units(assets, liabilities, cash):
        add('working_capital', assets.value - liabilities.value - cash.value,
            'Computed: Current Assets - Current Liabilities - Cash', assets, liabilities, cash, unit=assets.unit)

    capex, nwc, acquisitions = result.get('capex'), result.get('change_in_nwc'), result.get('acquisitions')
    reinvestment = None
    if matching_units(capex, da, nwc, acquisitions):
        reinvestment = add('reinvestment', capex.value - da.value + nwc.value + acquisitions.value,
            'Computed: Capex - D&A + Change in NWC + Acquisitions', capex, da, nwc, acquisitions, unit=capex.unit)
    elif capex is None:
        net_capex = find('net_capex')
        if matching_units(net_capex, nwc, acquisitions):
            reinvestment = add('reinvestment', net_capex.value + nwc.value + acquisitions.value,
                'Computed: Reported Net Capex + Change in NWC + Acquisitions',
                net_capex, nwc, acquisitions, unit=net_capex.unit)
    if matching_units(nopat, reinvestment):
        add('fcff', nopat.value - reinvestment.value, 'Computed: NOPAT - Reinvestment',
            nopat, reinvestment, unit=nopat.unit)
    net_income = result.get('net_income')
    net_borrowing = find('net_borrowing', 'net_debt_issued')
    if matching_units(net_income, reinvestment, net_borrowing):
        add('fcfe', net_income.value - reinvestment.value + net_borrowing.value,
            'Computed: Net Income - Reinvestment + Net Borrowing', net_income, reinvestment,
            net_borrowing, unit=net_income.unit)

    equity = find('book_equity', 'total_equity', 'shareholders_equity')
    invested = find('invested_capital')
    if invested is not None:
        result['invested_capital'] = invested
    elif matching_units(equity, debt, cash):
        invested = add('invested_capital', equity.value + debt.value - cash.value,
            'Computed: Book Equity + Debt - Cash', equity, debt, cash, unit=equity.unit)
    if matching_units(nopat, invested) and invested.value > 0:
        add('roic', nopat.value / invested.value, 'Computed: NOPAT / Reported Period-End Invested Capital', nopat, invested)
    if matching_units(net_income, equity) and equity.value > 0:
        add('roe', net_income.value / equity.value, 'Computed: Net Income / Reported Period-End Book Equity', net_income, equity)
    return result
