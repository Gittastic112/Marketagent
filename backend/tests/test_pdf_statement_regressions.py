"""Mock Data regressions for defects found in retained official report previews.

Values are deliberately small synthetic examples, not financial reference answers.
"""
import pytest

from app.services.pdf_financial_extraction import (
    _consolidate_candidates,
    _parse_pdf_financial_tables,
    _reporting_unit,
    _statement_line_candidates,
    _statement_years,
)


def rows(text, section="Consolidated Balance Sheet", currency="INR", scale="crore"):
    return _statement_line_candidates(
        page_text=text, page_number=1, section=section, currency=currency, scale=scale,
        page_width=1200, page_height=840, page=None,
    )


@pytest.mark.parametrize(("heading", "expected"), [
    ("Notes 2025-26 2024-25", (2026, 2025)),
    ("Year ended 2025–2026 2024–2025", (2026, 2025)),
    ("As at 31.03.2026 31.03.2025", (2026, 2025)),
    ("Particulars FY2025 FY2026", (2025, 2026)),
    ("Year ended 2026-03-31 2025-03-31", (2026, 2025)),
])
def test_fiscal_year_uses_end_of_reported_period(heading, expected):
    assert _statement_years(heading) == expected


@pytest.mark.parametrize(("heading", "expected"), [
    ("All amounts are in millions of Indian Rupee; except per share data", ("INR", "million")),
    ("` in ‘000s", ("INR", "thousand")),
    ("(000s omitted)\nSchedule No.\n` `", ("INR", "thousand")),
    ("(Rs. in millions)", ("INR", "million")),
    ("Amounts in USD millions", ("USD", "million")),
    ("(I in crore)", (None, "crore")),
    ("Amounts in crore", (None, "crore")),
    ("Amounts in NPR crore", (None, "crore")),
    ("Amounts in millions", (None, "million")),
    ("(000s omitted)", (None, "thousand")),
])
def test_explicit_money_units_and_unknown_currency(heading, expected):
    assert _reporting_unit(heading) == expected


def test_long_indian_comma_groups_are_not_split_or_promoted_as_generic_cash():
    result = rows("Schedule As at 31.03.2026 31.03.2025\nCash and Balances with Reserve Bank of India 6 123456,78,90 98765,43,21", scale="thousand")
    assert [(r.metric_code, r.value) for r in result] == [
        ("cash_and_balances_with_rbi", 1234567890), ("cash_and_balances_with_rbi", 987654321),
    ]
    assert all(r.unit == "INR thousand" for r in result)


def test_borrowings_retain_scope_and_are_never_summed_with_totals():
    result = rows("Notes As at March 31, 2026 March 31, 2025\nNon-current liabilities\nBorrowings 16 70 60\nCurrent liabilities\nBorrowings 20 30 25\nTotal borrowings 100 85\nTotal debt 120 105")
    result = _consolidate_candidates(result)
    current = [r for r in result if r.fiscal_year == 2026]
    assert {(r.metric_code, r.value) for r in current} == {
        ("noncurrent_borrowings", 70), ("current_borrowings", 30), ("borrowings", 100), ("debt", 120),
    }
    assert not any(r.source_locator_json["type"] == "pdf_reported_component_sum" for r in result)


def test_cash_flow_opening_closing_and_movements_do_not_become_balance_sheet_cash():
    result = rows("Year ended March 31, 2026 March 31, 2025\nCash and cash equivalents as at beginning of the year 50 40\nCash and cash equivalents as at end of the year (refer note 15) 70 50\nCash acquired on acquisition of subsidiary (Refer note 4(g)) 3 2", section="Consolidated Statement of Cash Flows")
    assert {(r.metric_code, r.value) for r in result if r.fiscal_year == 2026} == {
        ("cash_flow_cash_opening", 50), ("cash_flow_cash_closing", 70),
    }


def test_profit_attribution_restarts_after_oci_and_does_not_mix_comprehensive_income():
    result = rows("Year ended March 31, 2026 March 31, 2025\nProfit for the year 90 75\nOther comprehensive income 6 4\nProfit for the year attributable to: 90 75\nOwners of the Parent 70 60\nNCI 20 15\nOther comprehensive income attributable to:\nOwners of the Parent 5 3\nNCI 1 1\nTotal comprehensive income attributable to:\nOwners of the Parent 75 63\nNCI 21 16", section="Consolidated Statement of Profit and Loss")
    current = {(r.metric_code, r.value) for r in result if r.fiscal_year == 2026}
    assert current == {("group_profit", 90), ("net_income_parent", 70), ("net_income_nci", 20)}


def test_share_count_basis_is_explicit_and_basic_is_not_diluted():
    result = rows("Particulars FY2026 FY2025\nWeighted average number of equity shares used in computing basic earnings per equity 120 110\nshare\nWeighted average number of equity shares used in computing diluted earnings per equity 125 115\nshare")
    assert {(r.metric_code, r.value, r.unit) for r in result if r.fiscal_year == 2026} == {
        ("basic_shares", 120, "shares"), ("diluted_shares", 125, "shares"),
    }
    unknown = rows("FY2026 FY2025\nDiluted shares 125 115")
    assert all(r.unit is None and "reporting_unit_missing" in r.extraction_warnings for r in unknown)
    scaled = rows("FY2026 FY2025\nDiluted shares (in thousands) 125 115")
    assert all(r.unit == "shares thousand" for r in scaled)


def test_unexplained_extra_columns_and_partial_number_tokens_are_skipped():
    for values in ("10 20 30 40", "123,456abc 200", "1,234, 200", "10% 20%"):
        assert rows(f"FY2026 FY2025\nCash and cash equivalents {values}") == []
    result = rows("Notes FY2026 FY2025\nCash and cash equivalents 12 100 -")
    assert [(r.fiscal_year, r.value) for r in result] == [(2026, 100)]


def test_equal_values_on_separate_rows_are_not_deduplicated():
    result = rows("Notes FY2026 FY2025\nBorrowings 12 20 10\nBorrowings 18 20 10")
    assert len(_consolidate_candidates(result)) == 4


def mock_pdf(items, width=1200, height=840):
    """Minimal real PDF with Mock Data text at physical positions; no new dependency."""
    stream = "\n".join(
        f"BT /F1 9 Tf {x} {height-y} Td ({text.replace('(', chr(92)+'(').replace(')', chr(92)+')')}) Tj ET"
        for x, y, text in items
    ).encode("ascii")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    body = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(body)
    body += b"xref\n0 6\n0000000000 65535 f \n"
    body += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    return body + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()


def test_facing_pages_keep_values_years_and_absolute_highlight_coordinates():
    from app.services.financial_history_certification import _pdf_location_is_bounded
    body = mock_pdf([
        (30, 45, "Consolidated Balance Sheet"), (630, 45, "Consolidated Statement of Profit and Loss"),
        (30, 75, "Amounts in INR crore"), (630, 75, "Amounts in INR million"),
        (30, 100, "Notes 2025-26 2024-25"), (630, 100, "Notes 2025-26 2024-25"),
        (30, 130, "Cash and cash equivalents 10 123 100"), (630, 130, "Revenue from operations 25 900 800"),
        (30, 160, "Total assets 1000 900"), (630, 160, "Profit for the year 90 80"),
        (30, 820, "196"), (1150, 820, "197"),
    ])
    parsed = _parse_pdf_financial_tables(body)
    current = {(r.metric_code, r.value, r.unit) for r in parsed.candidates if r.fiscal_year == 2026}
    assert current == {("cash", 123, "INR crore"), ("total_assets", 1000, "INR crore"),
                       ("revenue", 900, "INR million"), ("group_profit", 90, "INR million")}
    revenue = next(r for r in parsed.candidates if r.metric_code == "revenue")
    assert revenue.source_locator_json["bounding_box"]["x0"] >= 600
    assert revenue.source_locator_json["page_width"] == 1200
    assert revenue.source_locator_json["region"] == 2
    assert revenue.source_section == "Consolidated Statement of Profit and Loss"
    assert all(_pdf_location_is_bounded(item.source_locator_json, parsed.page_count) for item in parsed.candidates)


def test_single_landscape_statement_is_not_split_by_page_shape():
    body = mock_pdf([(30, 45, "Consolidated Balance Sheet"), (30, 75, "Amounts in INR crore"),
        (30, 100, "Particulars"), (800, 100, "FY2026"), (950, 100, "FY2025"),
        (30, 130, "Cash and cash equivalents"), (800, 130, "123"), (950, 130, "100"),
        (1150, 820, "196")])
    parsed = _parse_pdf_financial_tables(body)
    assert {(r.fiscal_year, r.value) for r in parsed.candidates} == {(2026, 123), (2025, 100)}


def test_pre_associate_profit_and_cash_flow_adjustments_keep_their_basis():
    result = rows("FY2026 FY2025\nProfit After Tax 70 60\nShare of Profit of Associates 5 4\nProfit for the year 75 64", section="Consolidated Statement of Profit and Loss")
    assert {(r.metric_code, r.value) for r in result if r.fiscal_year == 2026} == {
        ("profit_after_tax_before_associates", 70), ("group_profit", 75),
    }
    cash_flow = rows("FY2026 FY2025\nFinance costs 8 7\nProfit before tax 90 80", section="Consolidated Statement of Cash Flows")
    assert {r.metric_code for r in cash_flow} == {"cash_flow_finance_costs", "cash_flow_pre_tax_income"}


def test_alphanumeric_note_and_unknown_currency_remain_explicit():
    result = rows("Schedule FY2026 FY2025\nMinority Interest 2A 120 110", currency=None, scale="thousand")
    assert {r.metric_code for r in result} == {"minority_interests"}
    assert all(r.unit is None and r.confidence_label == "medium" for r in result)


def test_repeated_identical_rows_have_distinct_highlight_positions():
    body = mock_pdf([(30, 45, "Consolidated Balance Sheet"), (30, 75, "Amounts in INR crore"),
        (30, 100, "FY2026 FY2025"), (30, 130, "Borrowings 120 100"), (30, 170, "Borrowings 120 100")], width=600)
    parsed = _parse_pdf_financial_tables(body)
    current = [r for r in parsed.candidates if r.fiscal_year == 2026]
    assert len(current) == 2
    assert current[1].source_locator_json["bounding_box"]["top"] - current[0].source_locator_json["bounding_box"]["top"] == 40
