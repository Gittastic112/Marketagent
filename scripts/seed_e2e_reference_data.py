"""Seed deterministic reference rows used only by the isolated browser test stack."""

from app.db.session import SessionLocal
from app.models import DamodaranDatasetFile, DamodaranMarginBenchmark


DATASET_CODE = "e2e_margin_fixture"


def main() -> None:
    with SessionLocal() as db:
        existing = db.query(DamodaranDatasetFile).filter_by(dataset_code=DATASET_CODE).first()
        if existing is not None:
            return

        dataset = DamodaranDatasetFile(
            uploaded_filename="mock-data-e2e-margin-fixture.xlsx",
            dataset_code=DATASET_CODE,
            country="United States",
            region="E2E",
            source_file_type="xlsx",
            notes="Mock Data used only for isolated browser workflow verification.",
        )
        db.add(dataset)
        db.flush()
        db.add_all(
            [
                DamodaranMarginBenchmark(
                    dataset_file_id=dataset.id,
                    industry_name="Software (System & Application)",
                    country="United States",
                    number_of_firms=10,
                    ebit_margin=0.20,
                ),
                DamodaranMarginBenchmark(
                    dataset_file_id=dataset.id,
                    industry_name="Semiconductor",
                    country="United States",
                    number_of_firms=10,
                    ebit_margin=0.18,
                ),
            ]
        )
        db.commit()


if __name__ == "__main__":
    main()
