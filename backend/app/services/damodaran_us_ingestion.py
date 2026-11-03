"""Explicit US snapshot intake into the existing versioned benchmark contracts."""
from hashlib import sha256
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService as Importer
from app.services.processing_runs import start_processing_run, complete_processing_run, fail_processing_run

US_SOURCES = {
    "beta_methods": ("betasUS-2026-01-05.xls", Importer.ingest_beta_methods_file),
    "wacc_methods": ("waccUS-2026-01-05.xls", Importer.ingest_wacc_methods_file),
    "margin": ("marginUS-2026-01-05.xls", Importer.ingest_margin_file),
    "capex": ("capexUS-2026-01-05.xls", Importer.ingest_capex_file),
    "roe": ("roeUS-2026-01-05.xls", Importer.ingest_roe_file),
    "working_capital": ("wcdataUS-2026-01-05.xls", Importer.ingest_wc_file),
}


def ingest_us_benchmarks(db: Session, data_dir: Path, only: set[str] | None = None) -> dict[str, int]:
    selected = set(US_SOURCES) if only is None else only
    if not selected or selected - US_SOURCES.keys():
        raise ValueError("Select supported US benchmark contracts only")
    counts = {}
    for key, (filename, importer) in US_SOURCES.items():
        if key not in selected:
            continue
        run = start_processing_run(db, run_type="damodaran_import", source_type="damodaran",
            metadata={"market": "US", "country": "United States", "source_file": filename, "contract": key})
        try:
            path = data_dir / filename
            raw = Importer._read_industry_averages(path)
            if str(raw.iloc[2, 5]).strip() != "US companies":
                raise ValueError("Expected explicit US-company source scope")
            source_date = pd.to_datetime(raw.iloc[0, 1]).date().isoformat()
            if source_date != "2026-01-05":
                raise ValueError("Source date differs from this registered snapshot; register a new dated version")
            digest = sha256(path.read_bytes()).hexdigest()
            prior = db.scalar(select(DamodaranDatasetFile).where(
                DamodaranDatasetFile.uploaded_filename == filename,
                DamodaranDatasetFile.country == "United States",
                DamodaranDatasetFile.source_sha256 == digest,
                DamodaranDatasetFile.row_count.is_not(None)))
            count = importer(db, str(path), "United States")
            complete_processing_run(db, run, fetched_count=count,
                created_count=0 if prior else count, skipped_duplicate_count=count if prior else 0,
                metadata_patch={"source_sha256": digest, "source_as_of": source_date})
            counts[key] = count
        except Exception:
            db.rollback()
            fail_processing_run(db, run, error_type="benchmark_import_failed",
                message="US benchmark import failed. Check the registered source date, scope and column contract.")
            raise
    return counts
