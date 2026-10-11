import pandas as pd
import math
from typing import Any
from pathlib import Path


def _read_industry_averages(path: Path) -> pd.DataFrame:
    return pd.read_excel(str(path), engine='xlrd', sheet_name='Industry Averages', header=None)


def _read_country_stats(path: Path) -> pd.DataFrame:
    return pd.read_excel(str(path), engine="xlrd", sheet_name=0, header=None)


def _find_header_row(df: pd.DataFrame) -> int:
    """
    Dynamically find the row that contains 'Industry Name'.
    """
    for i in range(min(20, len(df))):
        row_values = df.iloc[i].astype(str).str.strip().str.lower().tolist()
        if "industry name" in row_values or "industry" in row_values:
            return i
    return 0 # fallback


def _clean_value(val: Any) -> float | None:
    if pd.isna(val) or val == 'NA' or val == '':
        return None
    try:
        # If string with '%', convert to float
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
        # if it's already a float but nan/inf
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _require_columns(
    frame: pd.DataFrame,
    *,
    source_label: str,
    required: dict[str, str],
) -> dict[str, str]:
    def normalize(value: str) -> str:
        return " ".join(value.split()).casefold()

    columns = {normalize(str(column)): str(column) for column in frame.columns}
    resolved = {
        key: columns.get(normalize(source_column))
        for key, source_column in required.items()
    }
    missing = [required[key] for key, column in resolved.items() if column is None]
    if missing:
        raise ValueError(
            f"Missing required {source_label} column(s): " + ", ".join(missing)
        )
    return {key: column for key, column in resolved.items() if column is not None}


def _firm_count(value: Any) -> int | None:
    cleaned = _clean_value(value)
    return int(cleaned) if cleaned is not None else None


def _require_labeled_value(
    raw: pd.DataFrame,
    *,
    source_label: str,
    row_label: str,
    numeric_column: int | None = None,
) -> float:
    normalized_label = " ".join(row_label.split()).casefold()
    matching_rows = []
    for index, row in raw.iterrows():
        first_cell = " ".join(str(row.iloc[0]).split()).casefold()
        if first_cell == normalized_label:
            matching_rows.append(index)
    if len(matching_rows) != 1:
        raise ValueError(
            f"Expected one {source_label} row labeled {row_label}; "
            f"found {len(matching_rows)}"
        )
    if numeric_column is not None:
        cleaned = _clean_value(
            raw.iloc[matching_rows[0], numeric_column]
        )
        if cleaned is None:
            raise ValueError(
                f"Expected numeric {source_label} value for {row_label} in column {numeric_column}"
            )
        return cleaned
    values = [
        cleaned
        for value in raw.loc[matching_rows[0]].iloc[1:]
        if (cleaned := _clean_value(value))
        is not None
    ]
    if len(values) != 1:
        raise ValueError(
            f"Expected one numeric {source_label} value for {row_label}; "
            f"found {len(values)}"
        )
    return values[0]
