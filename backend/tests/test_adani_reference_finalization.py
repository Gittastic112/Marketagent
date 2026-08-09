from datetime import date

import pytest

from scripts.finalize_adani_reference_data import (
    EBIT_RECONSTRUCTIONS,
    _assert_ebit_components_on_page,
    _ebit_locator,
)


def test_apsez_operating_ebit_reconstruction_values() -> None:
    assert EBIT_RECONSTRUCTIONS[2023].value == 9408.74
    assert EBIT_RECONSTRUCTIONS[2024].value == 11975.46
    assert EBIT_RECONSTRUCTIONS[2025].value == 14042.44


def test_apsez_operating_ebit_locator_is_auditable_calculation() -> None:
    locator = _ebit_locator(EBIT_RECONSTRUCTIONS[2025])

    assert locator["type"] == "pdf_formula"
    assert locator["claim_type"] == "Calculation"
    assert locator["end"] == date(2025, 3, 31).isoformat()
    assert len(locator["components"]) == 5
    assert "other income" in locator["excluded"]


def test_apsez_ebit_components_must_share_the_declared_pdf_page() -> None:
    item = EBIT_RECONSTRUCTIONS[2025]
    rows = "\n".join(f"{label} {value:,.2f}" for label, value in item.components)
    _assert_ebit_components_on_page(f"[Page 465]\nheader\n[Page 466]\n{rows}\n[Page 542]\nnotes", item)

    with pytest.raises(ValueError, match="Other Expenses"):
        _assert_ebit_components_on_page(
            f"[Page 466]\n{rows.replace('Other Expenses 1,975.55', '')}",
            item,
        )
