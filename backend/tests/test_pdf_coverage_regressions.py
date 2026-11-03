"""Mock Data checks for explicit statement coverage and font-backed unit evidence."""
from types import SimpleNamespace

import pytest

from app.services import pdf_financial_extraction as parser


def rows(body, section="Consolidated Balance Sheet", currency="INR", scale="crore"):
    return parser._statement_line_candidates(
        page_text="Notes FY2026 FY2025\n" + body, page_number=1, section=section,
        currency=currency, scale=scale, page_width=600, page_height=840, page=None,
    )


def current(items):
    return {item.metric_code: (item.value, item.unit) for item in items if item.fiscal_year == 2026}


def test_bank_sections_disambiguate_repeated_total_rows_and_keep_deposits_separate():
    result = current(rows("CAPITAL AND LIABILITIES\nCapital 1 10 9\nReserves & Surplus 2 20 18\n"
        "Deposits 3 90 80\nBorrowings 4 30 20\nTOTAL 150 127\nASSETS\n"
        "Cash and Balances with Reserve Bank of India 6 15 12\n"
        "Balances with Banks and Money at Call & Short Notice 7 25 20\n"
        "Investments 8 30 20\nAdvances 9 80 75\nTOTAL 150 127"))
    assert result == {"share_capital": (10, "INR crore"), "reserves_surplus": (20, "INR crore"),
        "deposits": (90, "INR crore"), "borrowings": (30, "INR crore"),
        "total_liabilities_equity": (150, "INR crore"), "cash_and_balances_with_rbi": (15, "INR crore"),
        "balances_with_banks": (25, "INR crore"), "investments": (30, "INR crore"),
        "advances": (80, "INR crore"), "total_assets": (150, "INR crore")}
    assert rows("TOTAL 150 127") == []


def test_bank_income_expenses_and_parent_profit_do_not_become_revenue_or_ebit():
    result = current(rows("I. INCOME\nInterest earned 13 100 90\nOther income 14 20 15\nTOTAL 120 105\n"
        "II. EXPENDITURE\nInterest expended 15 60 50\nOperating expenses 16 20 15\n"
        "Provisions and contingencies 18 (9) 10 10\nTOTAL 90 75\nIII. PROFIT\n"
        "Consolidated Net Profit for the year before Minority Interest 30 30\n"
        "Less : Minority Interest 2 3\nConsolidated Net Profit for the year attributable to the group 28 27",
        section="Consolidated Profit and Loss Account"))
    assert result == {"interest_earned": (100, "INR crore"), "other_income": (20, "INR crore"),
        "total_income": (120, "INR crore"), "interest_expended": (60, "INR crore"),
        "operating_expenses": (20, "INR crore"), "provisions_contingencies": (10, "INR crore"),
        "total_expenses": (90, "INR crore"), "group_profit": (30, "INR crore"),
        "net_income_nci": (2, "INR crore"), "net_income_parent": (28, "INR crore")}


@pytest.mark.parametrize(("label", "metric"), [
    ("Total Current Assets", "current_assets"), ("Total Current Liabilities", "current_liabilities"),
    ("Total Equity and Liabilities", "total_liabilities_equity"),
    ("Total Equity", "total_equity_including_nci"), ("Other Equity", "other_equity"),
    ("Total Liabilities", "total_liabilities"),
])
def test_explicit_balance_sheet_totals_keep_their_scope(label, metric):
    assert current(rows(label + " 100 90")) == {metric: (100, "INR crore")}


@pytest.mark.parametrize(("label", "metric", "value"), [
    ("Net Cash Flow from Operating Activities", "operating_cash_flow", 100),
    ("Net cash generated from operating activities", "operating_cash_flow", 100),
    ("Net Cash Flow used in Investing Activities", "investing_cash_flow", -30),
    ("Net cash used in financing activities", "financing_cash_flow", -40),
    ("Purchase of property, plant and equipment", "ppe_cash_outflow", -20),
    ("Purchase of intangible assets", "intangibles_cash_outflow", -5),
    ("Payment towards spectrum", "spectrum_cash_outflow", -7),
    ("Net increase in the cash and cash equivalents", "cash_change", 30),
    ("Opening Balance of Cash and Cash Equivalents", "cash_flow_cash_opening", 50),
    ("Closing Balance of Cash and Cash Equivalents", "cash_flow_cash_closing", 80),
])
def test_cash_flow_coverage_preserves_signs_and_does_not_invent_generic_capex(label, metric, value):
    raw = f"({abs(value)})" if value < 0 else str(value)
    assert current(rows(f"{label} {raw} 10", section="Consolidated Cash Flow Statement")) == {
        metric: (value, "INR crore")}


def test_per_share_amounts_never_inherit_money_scale_and_do_not_become_share_counts():
    result = current(rows("Earnings per equity share (in INR)\nBasic 4.5 4.0\nDiluted 4.2 3.8",
        section="Consolidated Statement of Profit and Loss"))
    assert result == {"basic_eps": (4.5, "INR/share"), "diluted_eps": (4.2, "INR/share")}
    assert rows("Basic 4.5 4.0\nDiluted 4.2 3.8") == []


def test_weighted_average_share_note_retains_explicit_thousand_basis():
    result = current(rows("Weighted average shares outstanding for basic EPS (in thousands) 120 110\n"
        "Weighted average shares outstanding for diluted EPS (in thousands) 125 115", section="Earnings per share"))
    assert result == {"basic_shares": (120, "shares thousand"), "diluted_shares": (125, "shares thousand")}


def test_cash_flow_adjustments_and_bank_deposits_do_not_normalize_into_valuation_inputs():
    from app.services.accounting_normalization import FinancialReconciliationService

    canonical = {code for aliases in FinancialReconciliationService.CANONICAL_ALIASES.values() for code in aliases}
    assert not canonical.intersection({"deposits", "bank_borrowings", "cash_flow_cash_closing",
        "cash_flow_pre_tax_income", "ppe_cash_outflow", "interest_earned"})


def font_page(*, embedded=True, font="ABCDEF+ITFRupee", glyph="C", top=60):
    from pdfminer.psparser import LIT

    return SimpleNamespace(height=840, width=600,
        chars=[{"text": glyph, "fontname": font, "x0": 480, "x1": 487, "top": top, "bottom": top+7}],
        page_obj=SimpleNamespace(resources={"Font": {"F1": {"BaseFont": LIT(font),
            "FontDescriptor": {"FontFile2": object()} if embedded else {}}}}))


@pytest.mark.parametrize("glyph", ["C", "I", "J"])
def test_embedded_rupee_symbol_in_unit_header_retains_evidence(glyph):
    currency, scale, evidence = parser._page_reporting_unit(font_page(glyph=glyph), f"({glyph} in crore)")
    assert (currency, scale) == ("INR", "crore")
    assert evidence["basis"] == "embedded_rupee_symbol_font"
    assert evidence["symbols"][0]["text"] == glyph


@pytest.mark.parametrize("kwargs", [{"embedded": False}, {"font": "ABCDEF+NotRupee"},
    {"glyph": "X"}, {"top": 500}])
def test_font_names_and_body_symbols_alone_cannot_establish_currency(kwargs):
    currency, scale, evidence = parser._page_reporting_unit(font_page(**kwargs), "(C in crore)")
    assert currency is None and scale == "crore" and evidence is None


def test_explicit_currency_is_not_overridden_by_an_embedded_symbol():
    assert parser._page_reporting_unit(font_page(), "Amounts in USD millions")[:2] == ("USD", "million")


def test_balance_heading_with_layout_spacing_still_identifies_statement():
    section = parser._page_section("CONSOLIDATED BAL ANCE SHEET\nAs at March 31, 2026")
    assert current(rows("Capital 1 10 9\nDeposits 3 90 80", section=section)) == {
        "share_capital": (10, "INR crore"), "deposits": (90, "INR crore")}


def test_wrapped_parent_profit_keeps_full_source_and_bounded_highlight():
    from test_pdf_statement_regressions import mock_pdf
    body = mock_pdf([(30, 45, "Consolidated Profit and Loss Account"),
        (30, 75, "Amounts in INR crore"), (30, 100, "FY2026 FY2025"),
        (30, 130, "Consolidated profit/(loss) for the year attributable to the"),
        (30, 145, "Group 120 110")], width=600)
    parsed = parser._parse_pdf_financial_tables(body)
    item = next(r for r in parsed.candidates if r.metric_code == "net_income_parent" and r.fiscal_year == 2026)
    assert item.value == 120
    assert "Group 120 110" in item.source_text
    box = item.source_locator_json["bounding_box"]
    assert box is not None and box["bottom"] - box["top"] > 20


@pytest.mark.parametrize("label", [
    "Net profit for the year (before share in profit of\nassociates and minority interest) 120 110",
    "Net Profit for the year (before adjustment for Share in Profit of Associates and 120 110\nMinority Interest)",
])
def test_wrapped_pre_associate_profit_does_not_become_parent_income(label):
    assert current(rows(label, section="Consolidated Profit and Loss Account")) == {
        "profit_before_associates_nci": (120, "INR crore")}


def test_wrapped_share_label_and_local_scale_do_not_inherit_money_millions():
    result = current(rows("Weighted average number of equity shares for calculation of basic earnings per\n"
        "120 110\nshare (C) (in thousands)\n"
        "Weighted average number of equity shares for calculation of diluted earnings per\n"
        "125 115\nshare (D) (in thousands)", section="Notes", scale="million"))
    assert result == {"basic_shares": (120, "shares thousand"), "diluted_shares": (125, "shares thousand")}


def test_wrapped_icici_style_share_counts_are_actual_counts():
    result = current(rows("Weighted average number of equity shares outstanding used in\n"
        "computation of Basic EPS 120000 110000\n"
        "Weighted average number of equity shares outstanding used in\n"
        "computation of Diluted EPS 125000 115000", section="Notes", scale="million"))
    assert result == {"basic_shares": (120000, "shares"), "diluted_shares": (125000, "shares")}


def test_share_count_header_is_local_and_does_not_apply_to_later_notes():
    result = rows("(‘000)\nWeighted average shares outstanding for basic EPS 120 110\n"
        "Effect of dilution 5 5\nWeighted average shares outstanding for diluted EPS 125 115\n"
        "34. Other note\nDiluted shares 200 190", section="Notes", scale="million")
    assert [(r.metric_code, r.unit) for r in result if r.fiscal_year == 2026] == [
        ("basic_shares", "shares thousand"), ("diluted_shares", "shares thousand"), ("diluted_shares", None)]


def test_missing_font_resource_name_is_ignored():
    page = font_page()
    del page.page_obj.resources["Font"]["F1"]["BaseFont"]
    assert parser._page_reporting_unit(page, "(C in crore)") == (None, "crore", None)


@pytest.mark.parametrize("symbol", ["₹", "`"])
def test_explicit_eps_currency_does_not_require_a_monetary_scale(symbol):
    result = current(rows(f"Earnings per share\nBasic earnings per share ({symbol}) 4.5 4.0\n"
        f"Diluted earnings per share ({symbol}) 4.2 3.8", section="Notes", currency=None, scale=None))
    assert result == {"basic_eps": (4.5, "INR/share"), "diluted_eps": (4.2, "INR/share")}


def test_zero_notation_share_units_are_not_extra_value_columns():
    result = current(rows("Weighted average number of equity shares for calculation of basic earnings per share (C) (in ‘000) 120 110\n"
        "(in ‘000)\nWeighted average shares outstanding for diluted EPS 125 115", section="Notes", scale="million"))
    assert result == {"basic_shares": (120, "shares thousand"), "diluted_shares": (125, "shares thousand")}


@pytest.mark.parametrize("symbol", ["₹", "`"])
def test_explicit_rupee_prefixed_eps_values_are_complete_tokens(symbol):
    result = current(rows(f"Earnings per equity share\nBasic (in {symbol}) {symbol}4.5 {symbol}4.0\n"
        f"Diluted (in {symbol}) {symbol}4.2 {symbol}3.8", section="Consolidated Profit and Loss Account"))
    assert result == {"basic_eps": (4.5, "INR/share"), "diluted_eps": (4.2, "INR/share")}


@pytest.mark.parametrize("body", ["Basic (in USD) ₹4.5 ₹4.0", "Basic H4.5 H4.0",
    "Basic ₹4.5abc ₹4.0", "Basic ₹4.5% ₹4.0%"])
def test_unverified_currency_tokens_and_conflicting_eps_units_are_not_values(body):
    assert rows("Earnings per equity share\n" + body, section="Consolidated Profit and Loss Account") == []


@pytest.mark.parametrize("embedded", [True, False])
def test_eps_letter_glyph_requires_matching_embedded_font_and_retains_original(embedded):
    line = "Basic (in H) H4.5 H4.0"
    page = font_page(embedded=embedded, glyph="H", top=460)
    symbols = [{**page.chars[0], "x0": x, "x1": x+7} for x in (90, 450, 520)]
    page.search = lambda *a, **kw: [{"x0": 30, "x1": 550, "top": 460, "bottom": 468, "chars": symbols}]
    result = parser._statement_line_candidates(page_text="FY2026 FY2025\nEarnings per equity share\n"+line,
        page_number=1, section="Consolidated Profit and Loss Account", currency="INR", scale="thousand",
        page_width=600, page_height=840, page=page)
    if not embedded:
        assert result == []
        return
    assert current(result) == {"basic_eps": (4.5, "INR/share")}
    assert all(r.source_text == line for r in result)
    assert all(r.source_locator_json['unit_evidence']['symbols'] == symbols for r in result)
    assert all('currency_from_embedded_font_requires_review' in r.extraction_warnings for r in result)


def test_a_single_normal_letter_among_rupee_glyphs_blocks_eps_repair():
    page = font_page(glyph="H", top=460)
    page.search = lambda *a, **kw: [{"chars": [page.chars[0], page.chars[0],
        {**page.chars[0], "fontname": "NormalFont"}]}]
    result = parser._statement_line_candidates(page_text="FY2026 FY2025\nEarnings per equity share\nBasic (in H) H4.5 H4.0",
        page_number=1, section="Consolidated Profit and Loss Account", currency="INR", scale="thousand",
        page_width=600, page_height=840, page=page)
    assert result == []


def sidebar_pdf(*, repeated=True, extra_x=575, headers=True, extra_header=False):
    from test_pdf_statement_regressions import mock_pdf
    items = [(30,45,"Consolidated Cash Flow Statement"),(30,65,"Amounts in INR million")]
    items += [(420,95,"2026"),(500,95,"2025")] if headers else [(30,95,"FY2026 FY2025")]
    if extra_header:
        items += [(565,95,"Change")]
    items += [(30,155,"Net increase in cash and cash equivalents"),(420,155,"30"),(500,155,"20"),(extra_x,155,"02")]
    if repeated:
        items += [(extra_x,120,"01"),(extra_x,190,"03")]
    return mock_pdf(items,width=600)


def test_repeated_sidebar_numbers_outside_reported_columns_are_not_financial_values():
    result = parser._parse_pdf_financial_tables(sidebar_pdf())
    assert {(r.fiscal_year,r.value) for r in result.candidates} == {(2026,30),(2025,20)}
    assert all(r.unit == "INR million" for r in result.candidates)
    for item in result.candidates:
        assert item.source_text.endswith("30 20 02")
        evidence = item.source_locator_json['excluded_margin_number']
        assert evidence['text'] == '02' and evidence['x0'] == 575
        assert item.source_locator_json['bounding_box']['x1'] < evidence['x0']
        assert 'margin_number_excluded_requires_review' in item.extraction_warnings


@pytest.mark.parametrize("kwargs", [{"repeated":False},{"extra_x":535},{"headers":False},{"extra_header":True}])
def test_extra_numbers_without_margin_and_column_proof_remain_skipped(kwargs):
    assert parser._parse_pdf_financial_tables(sidebar_pdf(**kwargs)).candidates == ()
