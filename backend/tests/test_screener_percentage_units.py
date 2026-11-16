"""Mock Data workbook cells exercise explicit percentage storage conventions."""
import pytest
from openpyxl import Workbook

from app.providers.fundamentals.screener import ScreenerExcelParser


@pytest.mark.parametrize("raw,number_format,expected", [
    (20.5, "General", .205), (1, "General", .01), (.5, "General", .005),
    (0, "General", 0), (-.5, "General", -.005), (-20.5, "General", -.205),
    (.205, "0.0%", .205), (-.005, "0.00%", -.005),
    (.5, '0.0"%"', .005),
])
def test_percentage_storage_is_explicit_not_inferred_from_magnitude(tmp_path, raw, number_format, expected):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data Sheet"
    sheet.append(["Mock Data", "Mar 2025"])
    sheet.append(["OPM %", raw])
    sheet["B2"].number_format = number_format
    path = tmp_path / "mock-percentage.xlsx"
    workbook.save(path)
    workbook.close()
    candidate, = ScreenerExcelParser.parse_screener_excel(None, 1, 1, str(path), "INR")
    assert candidate.value == pytest.approx(expected)
    locator = candidate.source_locator_json
    assert locator["raw_value"] == raw
    assert locator["number_format"] == number_format
    assert locator["unit_transformation"] in {"percentage_points_divided_by_100", "excel_percentage_fraction"}
