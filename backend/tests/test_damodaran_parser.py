import io
import warnings
import pandas as pd
import pytest
from app.services.damodaran_parser import normalize_column_name, parse_damodaran_workbook

def test_normalize_column_name():
    assert normalize_column_name("Industry Name") == "industry_name"
    assert normalize_column_name("R&D / Sales") == "r_d_sales"
    assert normalize_column_name("  EV/EBITDA  ") == "ev_ebitda"
    assert normalize_column_name("1. Gross Margin") == "1_gross_margin"

def test_parse_damodaran_workbook():
    # We will simulate a raw excel sheet with headers not on the first row
    rows = [
        ["Updated: 2026-01-01", None, None],
        ["Region: Global", None, None],
        [None, None, None],
        ["Industry Name", "Number of Firms", "Gross Margin"],
        ["Software", "100", "0.80"],
        ["Hardware", "NA", "#DIV/0!"],
        ["Services", "50", "0"],
        [None, None, None],
        ["Total Market", "200", "0.40"] # Should be kept, but industry name is valid
    ]

    df_raw = pd.DataFrame(rows)

    # Save to BytesIO
    excel_buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="datetime.datetime.utcnow\\(\\) is deprecated",
            category=DeprecationWarning,
            module="openpyxl",
        )
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_raw.to_excel(writer, sheet_name='Industry Averages', index=False, header=False)

    excel_buffer.seek(0)
    file_bytes = excel_buffer.read()

    results = parse_damodaran_workbook(file_bytes)

    assert "Industry Averages" in results
    sheet_data = results["Industry Averages"]

    metadata = sheet_data["metadata"]
    assert len(metadata) == 2
    assert metadata[0] == "Updated: 2026-01-01"

    records = sheet_data["records"]
    assert len(records) == 4

    # Check software
    assert records[0]["industry_name"] == "Software"
    assert records[0]["number_of_firms"] == "100"
    assert records[0]["gross_margin"] == "0.80"

    # Check hardware (normalization)
    assert records[1]["industry_name"] == "Hardware"
    assert records[1]["number_of_firms"] is None
    assert records[1]["gross_margin"] is None

    # Check zero preservation
    assert records[2]["industry_name"] == "Services"
    assert records[2]["gross_margin"] == "0"
