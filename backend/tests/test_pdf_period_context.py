from app.services.pdf_financial_extraction import _statement_line_candidates, _table_candidates
from app.services.financial_period_context import pdf_period_context
import pytest


def rows(header):
    return _statement_line_candidates(page_text=f"Consolidated income statement\nUSD in millions\n{header}\nRevenue 100 90",
        page_number=1, section="Income statement", currency="USD", scale="million",
        page_width=600, page_height=800, page=None, period_type="annual")


def test_annual_document_does_not_make_quarterly_text_rows_annual():
    header = "Three months ended December 31, 2025 and December 31, 2024"
    candidates = rows(header)
    assert len(candidates) == 2
    assert {c.period_type for c in candidates} == {"quarterly"}
    assert all(header in c.source_locator_json["period_context"]["header_text"] for c in candidates)
    assert all("Three months" in c.source_column_label for c in candidates)


def test_missing_duration_is_unknown_and_original_header_is_retained():
    candidates = rows("2025 2024")
    assert len(candidates) == 2 and {c.period_type for c in candidates} == {"unknown"}
    assert all(c.source_locator_json["period_context"]["header_text"].endswith("2025 2024") for c in candidates)


def test_mixed_table_columns_keep_individual_duration():
    candidates = _table_candidates(matrix=[
        ["Metric", "Three months ended 2025", "Nine months ended 2025", "Year ended 2025"],
        ["Revenue", "10", "30", "40"]], rows=[], table_bbox=(0, 0, 500, 200),
        page_number=1, page_width=600, page_height=800, table_number=1,
        section="Income statement", currency="USD", scale="million", period_type="annual")
    assert [(c.value, c.period_type) for c in candidates] == [(10, "quarterly"), (30, "ytd"), (40, "annual")]


def test_merged_mixed_headers_without_column_mapping_are_held():
    candidates = _table_candidates(matrix=[
        ["Quarter ended and year ended", None, None], ["Metric", "2025", "2024"],
        ["Revenue", "10", "40"]], rows=[], table_bbox=(0, 0, 500, 200),
        page_number=1, page_width=600, page_height=800, table_number=1,
        section="Income statement", currency="USD", scale="million", period_type="annual")
    assert len(candidates) == 2 and {c.period_type for c in candidates} == {"unknown"}


def test_quarter_header_outside_table_overrules_fy_column_label():
    candidates = _table_candidates(matrix=[["Metric", "FY2025", "FY2024"], ["Revenue", "10", "9"]],
        rows=[], table_bbox=(0, 0, 500, 200), page_number=1, page_width=600, page_height=800,
        table_number=1, section="Income statement", currency="USD", scale="million", period_type="annual",
        page_text="Three months ended December 31\nMetric FY2025 FY2024\nRevenue 10 9")
    assert len(candidates) == 2 and {c.period_type for c in candidates} == {"quarterly"}


@pytest.mark.parametrize("header", ["Five months ended 2025", "11 months ended 2025", "Months ended 2025", "13 months ended 2025"])
def test_unresolved_month_duration_cannot_fall_back_to_fy_annual(header):
    assert pdf_period_context("FY2025", header, "annual", explicit_column=True)["period_type"] == "unknown"
