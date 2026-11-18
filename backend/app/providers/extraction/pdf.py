"""Adapters emit original-page tables; existing financial rules interpret them.

Called only in the bounded worker. Original PDFs are never rewritten.
"""
from dataclasses import asdict
from pathlib import Path
import re
from types import SimpleNamespace


def _camelot(path: str, pages: list[int], geometry: dict) -> list[dict]:
    import camelot

    result = []
    for table in camelot.read_pdf(path, pages=",".join(map(str, pages)), flavor="stream", parallel=False, suppress_stdout=True):
        page = int(table.page)
        height = geometry[page][1]
        x0, y0, x1, y1 = map(float, table._bbox)
        cells = [[(float(c.x1), height - float(c.y2), float(c.x2), height - float(c.y1)) for c in row] for row in table.cells]
        result.append({"page": page, "matrix": table.df.values.tolist(), "bbox": [x0, height - y1, x1, height - y0],
            "cells": cells, "provider_locator": {"table_order": table.order, "origin": "bottom_left", "original_bbox": list(table._bbox)}})
    return result


def _docling(path: str, pages: list[int], geometry: dict, model_dir: str) -> list[dict]:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions(artifacts_path=Path(model_dir), enable_remote_services=False,
        allow_external_plugins=False, document_timeout=40, do_ocr=True, do_table_structure=True)
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
    result = []
    for page in pages:
        document = converter.convert(path, page_range=(page, page)).document
        for table in document.tables:
            if not table.prov:
                continue
            prov = table.prov[0]
            actual_page = int(prov.page_no)
            if actual_page not in pages:
                raise ValueError("Unexpected page provenance")
            box = prov.bbox.to_top_left_origin(page_height=geometry[actual_page][1])
            frame = table.export_to_dataframe(doc=document)
            matrix = [[str(value) for value in frame.columns], *frame.fillna("").astype(str).values.tolist()]
            result.append({"page": actual_page, "matrix": matrix, "bbox": [box.l, box.t, box.r, box.b],
                "cells": [], "provider_locator": {"self_ref": table.self_ref, "provenance": prov.model_dump(mode="json")}})
    return result


def _marker(path: str, pages: list[int], geometry: dict) -> list[dict]:
    from bs4 import BeautifulSoup
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    config = ConfigParser({"output_format": "json", "use_llm": False,
        "page_range": ",".join(str(page - 1) for page in pages), "pdftext_workers": 1})
    converter = PdfConverter(config=config.generate_config_dict(), artifact_dict=create_model_dict(),
        processor_list=config.get_processors(), renderer=config.get_renderer(), llm_service=None)
    rendered = converter(path)
    result = []

    def walk(block, page):
        if str(block.block_type).split(".")[-1] == "Table":
            soup = BeautifulSoup(block.html, "html.parser")
            for table in soup.find_all("table"):
                # Merged cells require a separate reviewed normalization contract.
                if table.find(attrs={"rowspan": True}) or table.find(attrs={"colspan": True}):
                    continue
                matrix = [[cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"], recursive=False)]
                          for row in table.find_all("tr")]
                result.append({"page": page, "matrix": matrix, "bbox": list(block.bbox), "cells": [],
                    "provider_locator": {"block_id": block.id, "coordinate_basis": "marker_page_points"}})
        for child in block.children or []:
            walk(child, page)

    for page_block in rendered.children:
        match = re.search(r"/page/(\d+)", str(page_block.id))
        if not match:
            raise ValueError("Unknown Marker page identity")
        page = int(match.group(1)) + 1
        if page not in pages:
            raise ValueError("Unexpected Marker page")
        walk(page_block, page)
    return result


def parse_pdf(adapter: str, content: bytes, pages: list[int], model_dir: str | None, *, period_type: str = "unknown") -> dict:
    import pypdfium2 as pdfium

    if not content.startswith(b"%PDF-") or adapter not in {"camelot", "docling", "marker"}:
        raise ValueError
    path = Path("source.pdf")
    path.write_bytes(content)
    geometry, page_text = {}, {}
    with pdfium.PdfDocument(content) as pdf:
        page_count = len(pdf)
        if page_count > 1000 or any(p < 1 or p > page_count for p in pages):
            raise ValueError
        for number in pages:
            page = pdf[number - 1]
            try:
                geometry[number] = tuple(map(float, page.get_size()))
                textpage = page.get_textpage()
                try:
                    page_text[number] = textpage.get_text_range()
                finally:
                    textpage.close()
            finally:
                page.close()
    if adapter == "camelot":
        tables = _camelot(str(path), pages, geometry)
    elif adapter == "docling":
        tables = _docling(str(path), pages, geometry, model_dir)
    else:
        tables = _marker(str(path), pages, geometry)
    return {"tables": tables, "page_count": page_count, "scanned_pages": pages,
        "pages": {str(p): {"width": geometry[p][0], "height": geometry[p][1], "text": page_text[p]} for p in pages}}


def map_pdf_tables(data: dict, *, adapter: str, period_type: str) -> dict:
    """Interpret bounded neutral extraction output in the application's core env."""
    import math
    from app.services.pdf_financial_extraction import _table_candidates, _reporting_unit, _page_section

    pages, tables, page_data = data["scanned_pages"], data["tables"], data["pages"]
    if not isinstance(tables, list) or len(tables) > 200 or len(pages) > 20 or period_type not in {"annual", "quarterly", "unknown"}:
        raise ValueError
    total_cells = 0
    candidates = []
    per_page_counts = {}
    for table in tables:
        if (not isinstance(table["matrix"], list) or len(table["matrix"]) > 1000
                or any(not isinstance(row, list) or len(row) > 100 for row in table["matrix"])):
            raise ValueError
        page = table["page"]
        if page not in pages:
            raise ValueError
        info = page_data[str(page)]
        if any(not isinstance(info[key], (int, float)) or not math.isfinite(info[key]) or info[key] <= 0 for key in ("width", "height")):
            raise ValueError
        total_cells += sum(len(row) for row in table["matrix"])
        if total_cells > 100000 or any(cell is not None and (not isinstance(cell, str) or len(cell) > 8000) for row in table["matrix"] for cell in row):
            raise ValueError
        if len(table["bbox"]) != 4 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in table["bbox"]):
            raise ValueError
        per_page_counts[page] = per_page_counts.get(page, 0) + 1
        index = per_page_counts[page]
        text = info["text"]
        # OCR table headings remain available even when the original has no text layer.
        table_text = "\n".join(" | ".join(str(cell or "") for cell in row) for row in table["matrix"])
        currency, scale = _reporting_unit(text + "\n" + table_text)
        rows = [SimpleNamespace(cells=row) for row in table["cells"]]
        parsed = _table_candidates(matrix=table["matrix"], rows=rows, table_bbox=tuple(table["bbox"]),
            page_number=page, page_width=info["width"], page_height=info["height"], table_number=index,
            section=_page_section(text), currency=currency, scale=scale, period_type=period_type, page_text=text)
        for item in parsed:
            value = asdict(item)
            value["source_locator_json"].update(adapter=adapter, provider_locator=table["provider_locator"],
                coordinate_system="marker_native_points" if adapter == "marker" else "top_left_pdf_points")
            value["confidence_label"] = "medium"
            candidates.append(value)
    return {"candidates": candidates, "page_count": data["page_count"], "scanned_pages": pages,
        "table_count": len(tables), "raw_text": "\n\n".join(f"[Page {p}]\n{page_data[str(p)]['text']}" for p in pages),
        "warnings": ["EXTRACTED_VALUES_REQUIRE_SOURCE_REVIEW", *(["NO_SUPPORTED_FINANCIAL_TABLES"] if not candidates else []),
                     *(["MERGED_MARKER_TABLES_NOT_MAPPED"] if adapter == "marker" else [])]}
