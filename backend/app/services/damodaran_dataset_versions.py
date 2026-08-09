from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.damodaran import DamodaranDatasetFile
from app.services.damodaran_coverage import DAMODARAN_APPLICATION_COVERAGE


@dataclass(frozen=True, slots=True)
class DamodaranSourceProvenance:
    filename: str
    source_sha256: str
    source_byte_size: int
    source_as_of: str
    date_confidence: str
    canonical_source_path: str | None


@dataclass(frozen=True, slots=True)
class DatasetVersionStart:
    dataset_file: DamodaranDatasetFile
    is_idempotent: bool
    row_count: int | None


class DatasetVersionIntegrityError(ValueError):
    pass


def source_provenance_from_bytes(
    filename: str,
    contents: bytes,
) -> DamodaranSourceProvenance:
    spec = next(
        (
            item
            for item in DAMODARAN_APPLICATION_COVERAGE
            if item.source_filename.casefold() == filename.casefold()
        ),
        None,
    )
    return DamodaranSourceProvenance(
        filename=filename,
        source_sha256=sha256(contents).hexdigest(),
        source_byte_size=len(contents),
        source_as_of=spec.source_as_of if spec is not None else "unknown",
        date_confidence=spec.date_confidence if spec is not None else "low",
        canonical_source_path=spec.canonical_path if spec is not None else None,
    )


def source_provenance_from_path(path: Path) -> DamodaranSourceProvenance:
    return source_provenance_from_bytes(path.name, path.read_bytes())


def active_dataset_ids():
    return select(DamodaranDatasetFile.id).where(DamodaranDatasetFile.is_active.is_(True))


class DamodaranDatasetVersionService:
    @staticmethod
    def begin_typed_import(
        db: Session,
        *,
        path: Path,
        dataset_code: str,
        country: str | None,
        benchmark_model: type,
    ) -> DatasetVersionStart:
        provenance = source_provenance_from_path(path)
        existing = db.scalar(
            select(DamodaranDatasetFile)
            .where(
                DamodaranDatasetFile.dataset_code == dataset_code,
                DamodaranDatasetFile.country == country,
                DamodaranDatasetFile.source_sha256 == provenance.source_sha256,
                DamodaranDatasetFile.row_count.is_not(None),
            )
            .order_by(DamodaranDatasetFile.id.desc())
            .limit(1)
        )
        if existing is not None:
            actual_count = int(
                db.query(benchmark_model)
                .filter(benchmark_model.dataset_file_id == existing.id)
                .count()
            )
            if existing.row_count != actual_count:
                raise DatasetVersionIntegrityError(
                    f"Stored row count mismatch for dataset version {existing.id}: "
                    f"expected {existing.row_count}, found {actual_count}"
                )
            if not existing.is_active:
                DamodaranDatasetVersionService.complete_typed_import(
                    db,
                    dataset_file=existing,
                    row_count=actual_count,
                )
            return DatasetVersionStart(
                dataset_file=existing,
                is_idempotent=True,
                row_count=actual_count,
            )

        record = DamodaranDatasetFile(
            uploaded_filename=path.name,
            dataset_code=dataset_code,
            country=country,
            source_file_type=path.suffix.lstrip(".").lower(),
            source_sha256=provenance.source_sha256,
            source_byte_size=provenance.source_byte_size,
            source_as_of=provenance.source_as_of,
            date_confidence=provenance.date_confidence,
            canonical_source_path=provenance.canonical_source_path,
            import_kind="typed",
            is_active=False,
        )
        db.add(record)
        db.flush()
        return DatasetVersionStart(
            dataset_file=record,
            is_idempotent=False,
            row_count=None,
        )

    @staticmethod
    def complete_typed_import(
        db: Session,
        *,
        dataset_file: DamodaranDatasetFile,
        row_count: int,
    ) -> None:
        now = datetime.now(UTC)
        prior_versions = list(
            db.scalars(
                select(DamodaranDatasetFile).where(
                    DamodaranDatasetFile.dataset_code == dataset_file.dataset_code,
                    DamodaranDatasetFile.country == dataset_file.country,
                    DamodaranDatasetFile.id != dataset_file.id,
                    DamodaranDatasetFile.is_active.is_(True),
                )
            )
        )
        for prior in prior_versions:
            prior.is_active = False
            prior.superseded_at = now

        dataset_file.row_count = row_count
        dataset_file.is_active = True
        dataset_file.superseded_at = None
        db.commit()
