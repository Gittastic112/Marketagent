import math

import pytest

from app.services.financial_metric_derivations import derive_reported_metrics


def money(values, unit='INR crores'):
    return {code: (value, unit) for code, value in values.items()}


def complete_inputs():
    return money({'ebit':200, 'tax_expense':40, 'pre_tax_income':160,
        'net_income':120, 'capex':80, 'depreciation':30,
        'change_in_working_capital':10, 'acquisitions':0,
        'net_borrowing':15, 'book_equity':500, 'debt':100,
        'cash':50, 'current_assets':250, 'current_liabilities':100})


def test_partial_bank_statement_does_not_manufacture_cash_flows_or_returns():
    # Retained HDFC FY2025 labels; the bank's reported categories are deliberately
    # not interchangeable with operating-company EBIT, debt or available cash.
    values = money({'net_income_parent':70792.25, 'group_profit':73440.17,
        'deposits':2710898.23, 'borrowings':634605.57,
        'cash_and_balances_with_rbi':144390.25, 'share_capital':765.22,
        'reserves_surplus':517218.98})
    actual = derive_reported_metrics(values)
    assert set(actual) == {'net_income'}
    assert actual['net_income'].value == 70792.25
    assert actual['net_income'].source_codes == ('net_income_parent',)


def test_complete_source_basis_produces_dated_arithmetic_and_debt_cash_flow():
    actual = derive_reported_metrics(complete_inputs())
    assert actual['effective_tax_rate'].value == .25
    assert actual['nopat'].value == 150
    assert actual['working_capital'].value == 100
    assert actual['reinvestment'].value == 60
    assert actual['fcff'].value == 90
    assert actual['fcfe'].value == 75
    assert actual['invested_capital'].value == 550
    assert actual['roe'].value == .24
    assert actual['roic'].value == pytest.approx(150/550)
    assert actual['fcfe'].unit == 'INR crores'
    assert 'net_borrowing' in actual['fcfe'].source_codes
    assert 'Period-End' in actual['roe'].notes


@pytest.mark.parametrize('missing', ['capex','depreciation','change_in_working_capital','acquisitions'])
def test_each_missing_reinvestment_component_remains_unavailable(missing):
    values = complete_inputs()
    del values[missing]
    actual = derive_reported_metrics(values)
    assert not {'reinvestment','fcff','fcfe'} & actual.keys()


def test_missing_tax_and_net_borrowing_are_not_implicit_assumptions():
    values = complete_inputs()
    del values['tax_expense']
    del values['net_borrowing']
    actual = derive_reported_metrics(values)
    assert not {'effective_tax_rate','nopat','fcff','fcfe','roic'} & actual.keys()
    assert actual['reinvestment'].value == 60


def test_explicit_zero_is_preserved_but_zero_denominators_are_unavailable():
    values = complete_inputs()
    values.update(money({'ebit':0, 'net_income':0, 'capex':0, 'depreciation':0,
        'change_in_working_capital':0, 'net_borrowing':0, 'book_equity':0, 'invested_capital':0}))
    actual = derive_reported_metrics(values)
    assert all(actual[code].value == 0 for code in ('nopat','reinvestment','fcff','fcfe'))
    assert not {'roic','roe'} & actual.keys()


def test_conflicting_units_and_nonfinite_inputs_cannot_create_derived_facts():
    values = complete_inputs()
    values['capex'] = (80,'INR million')
    values['ebit'] = (math.inf,'INR crores')
    actual = derive_reported_metrics(values)
    assert not {'ebit','ebitda','nopat','reinvestment','fcff','fcfe','roic'} & actual.keys()


def test_debt_components_preserve_actual_sources_and_need_matching_units():
    values = money({'current_debt':20,'long_term_debt_noncurrent':80,'cash':50})
    actual = derive_reported_metrics(values)
    assert actual['debt'].value == 100
    assert actual['net_debt'].value == 50
    assert actual['net_debt'].source_codes == ('current_debt','long_term_debt_noncurrent','cash')
    values['long_term_debt_noncurrent'] = (80,'USD million')
    assert 'debt' not in derive_reported_metrics(values)


def test_reported_net_capex_is_not_reduced_by_depreciation_twice():
    values = complete_inputs()
    del values['capex']
    values['net_capex'] = (50, 'INR crores')
    actual = derive_reported_metrics(values)
    assert 'capex' not in actual
    assert actual['reinvestment'].value == 60
    assert actual['fcfe'].value == 75
    assert actual['reinvestment'].source_codes == ('net_capex', 'change_in_working_capital', 'acquisitions')
