import pandas as pd
import numpy as np
import re
import warnings
from typing import Dict, Any

def normalize_column_name(col: str) -> str:
    """Normalize a column name to snake_case."""
    if not isinstance(col, str):
        col = str(col)
    col = col.strip()
    # Replace non-alphanumeric with underscore
    col = re.sub(r'[^a-zA-Z0-9]', '_', col)
    # Collapse multiple underscores
    col = re.sub(r'_+', '_', col)
    col = col.lower()
    return col.strip('_')

def parse_damodaran_workbook(file_bytes: bytes) -> Dict[str, Any]:
    """
    Parses a Damodaran excel workbook into a structured dictionary.

    Rules implemented:
    - Finds the header row dynamically instead of hardcoding row 8.
    - Extracts metadata rows above the header.
    - Normalizes "NA", blanks, errors to null.
    - Preserves zeros.
    - Handles duplicate column names.
    - Normalizes columns to snake_case.
    """
    import io
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="datetime.datetime.utcnow\\(\\) is deprecated",
                category=DeprecationWarning,
                module="openpyxl",
            )
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}")

    results = {}
    for sheet_name in excel_file.sheet_names:
        df_raw = excel_file.parse(sheet_name, header=None)

        # Find header row
        header_row_idx = None
        for idx, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower().str.strip().tolist()
            if "industry name" in row_str or "country" in row_str:
                header_row_idx = idx
                break

        if header_row_idx is None:
            # Skip sheets that don't have our expected headers
            continue

        # Extract metadata
        metadata = []
        for i in range(header_row_idx):
            meta_row = df_raw.iloc[i].dropna().astype(str).tolist()
            if meta_row:
                metadata.append(" | ".join(meta_row))

        # Slice dataframe to data rows
        df = df_raw.iloc[header_row_idx+1:].copy()

        # Set and clean columns
        raw_columns = df_raw.iloc[header_row_idx].fillna('Unnamed').astype(str).tolist()

        seen = {}
        unique_cols = []
        for c in raw_columns:
            clean = normalize_column_name(c)
            if clean in seen:
                seen[clean] += 1
                unique_cols.append(f"{clean}_{seen[clean]}")
            else:
                seen[clean] = 0
                unique_cols.append(clean)

        df.columns = unique_cols

        # Drop rows where the primary key (industry_name or country) is missing or represents aggregate
        if 'industry_name' in df.columns:
            df = df.dropna(subset=['industry_name'])
            # Do not treat industry aggregate data as company-level data
            # Damodaran often has a "Total Market" or "Global" row at the bottom.
            # We preserve it, but the caller should be aware it's an aggregate.
        elif 'country' in df.columns:
            df = df.dropna(subset=['country'])

        # Normalization
        bad_values = ['NA', 'N.A.', 'N/A', '#DIV/0!', '#VALUE!', '#NAME?', '']
        df = df.replace(bad_values, np.nan)

        # Also clean up strings that might contain these values
        for col in df.columns:
            if df[col].dtype == object:
                # Strip whitespace and replace specific strings
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                df[col] = df[col].replace(bad_values, np.nan)

        # Convert NaN to None to output valid JSON nulls
        df = df.where(pd.notnull(df), None)

        records = df.to_dict(orient='records')

        results[sheet_name] = {
            "metadata": metadata,
            "records": records
        }

    if not results:
        raise ValueError("Could not find any sheet with 'Industry Name' or 'Country' header.")

    return results
