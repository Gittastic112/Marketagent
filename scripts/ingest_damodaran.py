import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.models.damodaran import DamodaranDatasetFile
from app.services.damodaran_coverage import build_damodaran_coverage_report
from app.services.damodaran_ingestion import DamodaranBenchmarkIngestionService
from app.services.macro_sensitivity_ingestion import MacroSensitivityIngestionService
from sqlalchemy import select

DATA_DIR = Path("/workspace/data/damodaran/raw")
COUNTRY = "India"

SOURCE_CODES = (
    "margin",
    "capex",
    "working_capital",
    "dividend",
    "fcfe",
    "roe",
    "macro",
    "macro_duration",
    "volatility",
    "pe",
    "pbv",
    "ps",
    "vebitda",
    "country_stats",
)


def print_active_version(db, dataset_code: str, country: str | None) -> None:
    version = db.scalar(
        select(DamodaranDatasetFile)
        .where(
            DamodaranDatasetFile.dataset_code == dataset_code,
            DamodaranDatasetFile.country == country,
            DamodaranDatasetFile.is_active.is_(True),
        )
        .order_by(DamodaranDatasetFile.id.desc())
        .limit(1)
    )
    if version is None:
        print("No active dataset version was found.")
        return
    source_hash = version.source_sha256 or "missing"
    print(
        f"Active version #{version.id}: sha256={source_hash}, "
        f"source_as_of={version.source_as_of or 'unknown'}, rows={version.row_count}."
    )


def print_coverage_summary(db) -> None:
    report = build_damodaran_coverage_report(db)
    print(
        "Coverage summary: "
        f"supported={report['supported_count']}, partial={report['partial_count']}, "
        f"unsupported={report['unsupported_count']}, typed_sources={report['ingested_count']}, "
        f"typed_rows={report['typed_record_count']}."
    )
    print(
        "Provenance summary: "
        f"complete={report['provenance_complete_count']}, "
        f"partial={report['provenance_partial_count']}, "
        f"missing={report['provenance_missing_count']}, "
        f"hash_mismatch={report['provenance_hash_mismatch_count']}."
    )


def run_ingestion(only: set[str] | None = None):
    if not DATA_DIR.exists():
        print(f"Data directory {DATA_DIR} does not exist.")
        return

    def selected(source_code: str) -> bool:
        return only is None or source_code in only

    db = SessionLocal()
    try:
        margin_file = DATA_DIR / "marginIndia.xls"
        if selected("margin") and margin_file.exists():
            print(f"Ingesting {margin_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_margin_file(db, str(margin_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "margins", COUNTRY)

        capex_file = DATA_DIR / "capexIndia.xls"
        if selected("capex") and capex_file.exists():
            print(f"Ingesting {capex_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_capex_file(db, str(capex_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "capex", COUNTRY)

        wc_file = DATA_DIR / "wcdataIndia.xls"
        if selected("working_capital") and wc_file.exists():
            print(f"Ingesting {wc_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_wc_file(db, str(wc_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "working_capital", COUNTRY)

        div_file = DATA_DIR / "divfundIndia.xls"
        if selected("dividend") and div_file.exists():
            print(f"Ingesting {div_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_dividend_file(db, str(div_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "dividends", COUNTRY)

        fcfe_file = DATA_DIR / "divfcfeIndia.xls"
        if selected("fcfe") and fcfe_file.exists():
            print(f"Ingesting {fcfe_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_fcfe_file(db, str(fcfe_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "fcfe", COUNTRY)

        roe_file = DATA_DIR / "roeIndia.xls"
        if selected("roe") and roe_file.exists():
            print(f"Ingesting {roe_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_roe_file(db, str(roe_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "roe", COUNTRY)

        macro_file = DATA_DIR / "macro.xls"
        if selected("macro") and macro_file.exists():
            print(f"Ingesting {macro_file}...")
            count = MacroSensitivityIngestionService.ingest_macro_file(db, str(macro_file))
            print(f"Ingested {count} macro observations.")

        macrodur_file = DATA_DIR / "macrodur.xls"
        if selected("macro_duration") and macrodur_file.exists():
            print(f"Ingesting {macrodur_file}...")
            macro_count = MacroSensitivityIngestionService.ingest_macro_file(db, str(macrodur_file))
            sector_count = MacroSensitivityIngestionService.ingest_sector_sensitivity_file(db, str(macrodur_file))
            print(f"Ingested {macro_count} macro observations and {sector_count} sector sensitivity records.")

        optvar_file = DATA_DIR / "optvarIndia.xls"
        if selected("volatility") and optvar_file.exists():
            print(f"Ingesting {optvar_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_volatility_file(db, str(optvar_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "volatility", COUNTRY)

        pe_file = DATA_DIR / "peIndia.xls"
        if selected("pe") and pe_file.exists():
            print(f"Ingesting {pe_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_pe_file(db, str(pe_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "pe", COUNTRY)

        pbv_file = DATA_DIR / "pbvIndia.xls"
        if selected("pbv") and pbv_file.exists():
            print(f"Ingesting {pbv_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_pbv_file(db, str(pbv_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "pbv", COUNTRY)

        ps_file = DATA_DIR / "psIndia.xls"
        if selected("ps") and ps_file.exists():
            print(f"Ingesting {ps_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_ps_file(db, str(ps_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "ps", COUNTRY)

        vebitda_file = DATA_DIR / "vebitdaIndia.xls"
        if selected("vebitda") and vebitda_file.exists():
            print(f"Ingesting {vebitda_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_vebitda_file(db, str(vebitda_file), COUNTRY)
            print(f"Ingested {count} records.")
            print_active_version(db, "vebitda", COUNTRY)

        countrystats_file = DATA_DIR / "countrystats.xls"
        if selected("country_stats") and countrystats_file.exists():
            print(f"Ingesting {countrystats_file}...")
            count = DamodaranBenchmarkIngestionService.ingest_countrystats_file(db, str(countrystats_file))
            print(f"Ingested {count} records.")
            print_active_version(db, "countrystats", "Global")

        # Add further workbooks only through source-specific, tested import contracts.
        print_coverage_summary(db)
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest reviewed Damodaran workbook contracts.")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=SOURCE_CODES,
        help="Ingest only the named source contracts instead of refreshing every available source.",
    )
    args = parser.parse_args()
    print("Starting Damodaran benchmark ingestion...")
    run_ingestion(set(args.only) if args.only else None)
    print("Done.")
