"""Conservative PDF period evidence; a document category is not a column duration."""
import re


def _scopes(text: str) -> set[str]:
    text = re.sub(r"[-\s]+", " ", text.lower())
    result = set()
    if re.search(r"\b(?:three|3) months?\b|\bquarter(?:s|ly)?\b|\bq[1-4]\b", text):
        result.add("quarterly")
    if re.search(r"\b(?:six|6|nine|9) months?\b|\bhalf year\b|\byear to date\b|\bytd\b", text):
        result.add("ytd")
    if re.search(r"\b(?:twelve|12) months?\b|\b(?:fiscal )?years? ended\b|\b(?:52|53) weeks?\b", text):
        result.add("annual")
    if re.search(r"\bas (?:at|of)\b", text):
        result.add("instant")
    for duration in re.finditer(r"\b(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve) )?months?\b", text):
        if duration.group(1) not in {"3", "three", "6", "six", "9", "nine", "12", "twelve"}:
            result.add("unknown")
    return result


def pdf_period_context(column_header: str, header_text: str, document_period: str, *, explicit_column=False) -> dict:
    column_scopes = _scopes(column_header)
    scopes = column_scopes if explicit_column and column_scopes else _scopes(header_text)
    if not scopes and re.search(r"\bFY\s*20\d{2}\b", column_header, re.I):
        scopes = {"annual"}
    scope = next(iter(scopes)) if len(scopes) == 1 else "unknown"
    period = "annual" if scope == "instant" and document_period == "annual" else scope
    if document_period != "annual" and period == "annual":
        period = document_period
    return {"reported_scope": scope, "period_type": period,
            "column_header": column_header, "header_text": header_text,
            "explicit_column": explicit_column}


def pdf_annual_scope_supported(candidate) -> bool:
    locator = candidate.source_locator_json or {}
    kind = locator.get("type", "")
    if not str(kind).startswith("pdf_") and not candidate.extraction_method.startswith("pdf_"):
        return True
    context = locator.get("period_context")
    if isinstance(context, dict):
        evidence = pdf_period_context(str(context.get("column_header", "")),
            str(context.get("header_text", "")), "annual", explicit_column=context.get("explicit_column") is True)
        return evidence["reported_scope"] in {"annual", "instant"}
    # Legacy text-row FY labels were synthesized from the year. They do not
    # prove duration. A legacy table's actual column label can still prove it.
    header = candidate.source_column_label or ""
    if kind == "pdf_text_row" and re.fullmatch(r"FY\d{4}", header, re.I):
        return False
    evidence = pdf_period_context(header, header, "annual", explicit_column=True)
    return evidence["reported_scope"] in {"annual", "instant"}
