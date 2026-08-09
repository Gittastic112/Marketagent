from typing import Dict, List, Tuple
import datetime
from sqlalchemy.orm import Session
from app.models.financial import FinancialExtractionCandidate

class ScreenerExcelParser:
    @staticmethod
    def parse_screener_excel(
        db: Session,
        company_id: int,
        raw_document_id: int,
        file_path: str,
        reporting_currency: str,
    ) -> List[FinancialExtractionCandidate]:
        """
        Parses a typical Screener.in Excel export (.xlsx).
        It targets the 'Data Sheet' tab to extract historical financial data.
        Returns a list of FinancialExtractionCandidate records to be inserted into the DB.
        """
        import openpyxl

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            if "Data Sheet" not in wb.sheetnames:
                raise ValueError("No 'Data Sheet' tab found in the uploaded Excel file. Are you sure this is a Screener.in export?")

            sheet = wb["Data Sheet"]
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")

        # Typical structure of Screener.in Data Sheet:
        # Row 1 is usually empty or has some title.
        # We need to find the block "Profit & Loss" or similar, but the columns are usually
        # laid out with years in one of the top rows.
        # Let's find the row that has year headers (e.g., 'Mar 2018', 'Mar 2019', 'TTM').

        year_headers: Dict[int, Tuple[int, str, str]] = {}
        header_row = None

        for r in range(1, 20):
            row_vals = [sheet.cell(row=r, column=c).value for c in range(1, sheet.max_column + 1)]
            for c_idx, val in enumerate(row_vals):
                c = c_idx + 1
                if isinstance(val, datetime.datetime):
                    # Sometimes dates are parsed as datetime objects
                    year_headers[c] = (val.year, "annual", val.strftime("%b %Y"))
                    header_row = r
                elif isinstance(val, str) and ("Mar 20" in val or "Dec 20" in val or "TTM" in val):
                    # "Mar 2023" -> 2023
                    if "TTM" in val:
                        year_headers[c] = (datetime.datetime.now().year, "ttm", val.strip())
                    else:
                        parts = val.strip().split(" ")
                        if len(parts) == 2 and parts[1].isdigit():
                            year_headers[c] = (int(parts[1]), "annual", val.strip())
                    header_row = r

        if not year_headers or not header_row:
            raise ValueError("Could not find column headers (e.g., 'Mar 2023') in the Data Sheet.")

        # Target metrics mapping
        # Screener row labels -> internal metric codes
        target_labels = {
            "Sales": "revenue",
            "Operating Profit": "ebitda",
            "OPM %": "opm",
            "Depreciation": "depreciation",
            "Interest": "interest",
            "Profit before tax": "ebt",
            "Net Profit": "net_income",
            "Share Capital": "share_capital",
            "Reserves": "reserves",
            "Borrowings": "debt",
            "Total Liabilities": "total_liabilities",
            "Fixed Assets": "fixed_assets",
            "CWIP": "cwip",
            "Investments": "investments",
            "Other Assets": "other_assets",
            "Total Assets": "total_assets",
            "Cash from Operating Activity": "cfo",
            "Cash from Investing Activity": "cfi",
            "Cash from Financing Activity": "cff",
            "Net Cash Flow": "net_cash_flow",
            "Debtor Days": "debtor_days",
            "Inventory Days": "inventory_days",
            "Days Payable": "days_payable",
            "ROCE %": "roce",
        }

        candidates = []

        for r in range(header_row + 1, sheet.max_row + 1):
            row_label_cell = sheet.cell(row=r, column=1).value
            if not row_label_cell or not isinstance(row_label_cell, str):
                continue

            label = row_label_cell.strip()

            # Remove trailing numbers like "Sales  12" (sometimes present)
            label_clean = " ".join([word for word in label.split() if not word.isdigit()])

            # We map directly if it starts with the target label
            matched_code = None
            for tl, code in target_labels.items():
                if label_clean.startswith(tl):
                    matched_code = code
                    break

            if not matched_code:
                continue

            # Iterate through columns and extract
            for col, (year, p_type, column_label) in year_headers.items():
                val = sheet.cell(row=r, column=col).value
                if val is not None and isinstance(val, (int, float)):
                    # Handle units: OPM % is usually percentage, ROCE % is percentage
                    # Screener exports them as absolute numbers (e.g., 20.5 for 20.5%)
                    final_val = float(val)
                    if matched_code in ("opm", "roce") and final_val > 1.0:
                        final_val = final_val / 100.0 # convert 20.5 to 0.205

                    candidate = FinancialExtractionCandidate(
                        company_id=company_id,
                        raw_document_id=raw_document_id,
                        metric_code=matched_code,
                        reported_label=label,
                        value=final_val,
                        unit=(
                            "percentage"
                            if matched_code in ("opm", "roce")
                            else "days"
                            if matched_code in ("debtor_days", "inventory_days", "days_payable")
                            else f"{reporting_currency} crore"
                        ),
                        fiscal_year=year,
                        period_type=p_type,
                        source_text=f"Screener.in Excel Row {r} Col {col}",
                        source_line_number=r,
                        source_page=None,
                        source_section="Data Sheet",
                        source_table_name="Data Sheet",
                        source_row_label=label,
                        source_column_label=column_label,
                        source_cell_reference=sheet.cell(row=r, column=col).coordinate,
                        source_locator_json={
                            "type": "spreadsheet_cell",
                            "sheet": "Data Sheet",
                            "row": r,
                            "column": col,
                            "cell": sheet.cell(row=r, column=col).coordinate,
                            "header_row": header_row,
                        },
                        extraction_warnings=None,
                        extraction_method="screener_excel_v1",
                        confidence_label="high",
                        review_status="needs_review"
                    )
                    candidates.append(candidate)

        return candidates
