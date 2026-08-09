from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from math import isfinite
from typing import Any, Mapping

import pypdfium2 as pdfium


MIN_RENDER_SCALE = 0.5
MAX_RENDER_SCALE = 2.0
MAX_RENDER_PIXELS = 16_000_000
PDF_REGION_COORDINATE_SYSTEM = "pdfplumber_top_left_points"
PAGE_DIMENSION_TOLERANCE_POINTS = 1.0


@dataclass(frozen=True)
class PdfRegionGeometry:
    page_number: int
    page_width: float
    page_height: float
    x0: float
    top: float
    x1: float
    bottom: float

    def as_json(self) -> dict[str, Any]:
        return {
            "page": self.page_number,
            "coordinate_system": PDF_REGION_COORDINATE_SYSTEM,
            "page_width": self.page_width,
            "page_height": self.page_height,
            "bounding_box": {
                "x0": self.x0,
                "top": self.top,
                "x1": self.x1,
                "bottom": self.bottom,
            },
        }


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"PDF region {field} must be a finite number")
    return float(value)


def parse_pdf_region_geometry(
    value: Mapping[str, Any] | None,
    *,
    source_page: int | None,
) -> PdfRegionGeometry:
    if value is None:
        raise ValueError("pdf_region requires bounding_box_json")
    if source_page is None:
        raise ValueError("pdf_region requires source_page")
    page_number = value.get("page")
    if isinstance(page_number, bool) or not isinstance(page_number, int):
        raise ValueError("PDF region page must be an integer")
    if page_number != source_page:
        raise ValueError("PDF region page must match source_page")
    if value.get("coordinate_system") != PDF_REGION_COORDINATE_SYSTEM:
        raise ValueError(
            f"PDF region coordinate_system must be {PDF_REGION_COORDINATE_SYSTEM}"
        )

    page_width = _finite_number(value.get("page_width"), "page_width")
    page_height = _finite_number(value.get("page_height"), "page_height")
    box = value.get("bounding_box")
    if not isinstance(box, Mapping):
        raise ValueError("PDF region bounding_box must be an object")
    x0 = _finite_number(box.get("x0"), "x0")
    top = _finite_number(box.get("top"), "top")
    x1 = _finite_number(box.get("x1"), "x1")
    bottom = _finite_number(box.get("bottom"), "bottom")

    if page_width <= 0 or page_height <= 0:
        raise ValueError("PDF region page dimensions must be positive")
    if x0 < 0 or top < 0 or x1 > page_width or bottom > page_height:
        raise ValueError("PDF region bounding_box must be inside the declared page")
    if x1 <= x0 or bottom <= top:
        raise ValueError("PDF region bounding_box must have positive area")
    return PdfRegionGeometry(
        page_number=page_number,
        page_width=page_width,
        page_height=page_height,
        x0=x0,
        top=top,
        x1=x1,
        bottom=bottom,
    )


def get_pdf_page_size(content: bytes, page_number: int) -> tuple[float, float]:
    if page_number < 1:
        raise ValueError("Page number must be at least 1")
    try:
        document = pdfium.PdfDocument(content)
    except Exception as exc:
        raise ValueError("Stored PDF asset could not be opened") from exc
    try:
        if page_number > len(document):
            raise IndexError("PDF page does not exist")
        page = document[page_number - 1]
        try:
            width, height = page.get_size()
            return float(width), float(height)
        finally:
            page.close()
    finally:
        document.close()


def validate_pdf_region_against_asset(
    value: Mapping[str, Any] | None,
    *,
    source_page: int | None,
    content: bytes,
) -> PdfRegionGeometry:
    geometry = parse_pdf_region_geometry(value, source_page=source_page)
    actual_width, actual_height = get_pdf_page_size(content, geometry.page_number)
    if (
        abs(actual_width - geometry.page_width) > PAGE_DIMENSION_TOLERANCE_POINTS
        or abs(actual_height - geometry.page_height) > PAGE_DIMENSION_TOLERANCE_POINTS
    ):
        raise ValueError("PDF region page dimensions do not match the stored PDF page")
    return geometry


def render_pdf_page_png(content: bytes, page_number: int, scale: float) -> bytes:
    if page_number < 1:
        raise ValueError("Page number must be at least 1")
    if scale < MIN_RENDER_SCALE or scale > MAX_RENDER_SCALE:
        raise ValueError("Render scale is outside the supported range")

    document = pdfium.PdfDocument(content)
    try:
        if page_number > len(document):
            raise IndexError("PDF page does not exist")
        page = document[page_number - 1]
        try:
            width, height = page.get_size()
            if width * scale * height * scale > MAX_RENDER_PIXELS:
                raise ValueError("Rendered PDF page would exceed the pixel limit")
            bitmap = page.render(scale=scale)
            try:
                image = bitmap.to_pil()
                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                return output.getvalue()
            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        document.close()
