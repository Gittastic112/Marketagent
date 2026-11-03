"""Seed valuation assumption methods from reviewed local workbooks.

This command intentionally contains no numeric fallback values. It delegates to
the same hash-versioned import contracts used by the full Damodaran ingestion
script.
"""

from pathlib import Path

from app.db.session import SessionLocal
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService


DATA_DIR = Path("/workspace/data/damodaran/raw")
COUNTRY = "India"


def seed_assumptions(db) -> dict[str, int]:
    sources = {
        "beta_methods": (
            DATA_DIR / "betaIndia.xls",
            lambda path: DamodaranBenchmarkIngestionService.ingest_beta_methods_file(
                db, str(path), COUNTRY
            ),
        ),
        "wacc_methods": (
            DATA_DIR / "waccIndia.xls",
            lambda path: DamodaranBenchmarkIngestionService.ingest_wacc_methods_file(
                db, str(path), COUNTRY
            ),
        ),
        "industry_tax_methods": (
            DATA_DIR / "taxrateIndia.xls",
            lambda path: DamodaranBenchmarkIngestionService.ingest_industry_tax_methods_file(
                db, str(path), COUNTRY
            ),
        ),
        "country_tax_methods": (
            DATA_DIR / "countrytaxrates.xls",
            lambda path: DamodaranBenchmarkIngestionService.ingest_country_tax_methods_file(
                db, str(path)
            ),
        ),
    }
    missing = [str(path) for path, _ in sources.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing reviewed assumption source file(s): " + ", ".join(missing)
        )
    return {name: importer(path) for name, (path, importer) in sources.items()}


def main() -> None:
    with SessionLocal() as db:
        counts = seed_assumptions(db)
    for source, count in counts.items():
        print(f"{source}: {count} records")


if __name__ == "__main__":
    main()
