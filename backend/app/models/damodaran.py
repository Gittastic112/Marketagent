from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from app.db.base import Base

class DamodaranDatasetFile(Base):
    __tablename__ = "damodaran_dataset_files"

    id = Column(Integer, primary_key=True, index=True)
    uploaded_filename = Column(String(255), nullable=False)
    dataset_code = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    date_updated = Column(DateTime(timezone=True), nullable=True)
    source_file_type = Column(String(50), nullable=False)
    source_sha256 = Column(String(64), nullable=True, index=True)
    source_byte_size = Column(Integer, nullable=True)
    source_as_of = Column(String(100), nullable=True)
    date_confidence = Column(String(20), nullable=False, default="unknown", server_default="unknown")
    canonical_source_path = Column(String(500), nullable=True)
    import_kind = Column(
        String(40),
        nullable=False,
        default="legacy_unknown",
        server_default="legacy_unknown",
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    row_count = Column(Integer, nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)
