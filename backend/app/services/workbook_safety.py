"""Preflight uploaded workbooks before invoking XML/spreadsheet parsers."""
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException

MAX_WORKBOOK_BYTES = 12 * 1024 * 1024


def validate_workbook_bytes(content: bytes) -> None:
    if not content or len(content) > MAX_WORKBOOK_BYTES:
        raise HTTPException(413, "Workbook must contain data and be at most 12 MiB.")
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return  # Legacy XLS, still subject to the byte cap and parser validation.
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(item.file_size for item in entries) > 64 * 1024 * 1024:
                raise HTTPException(413, "Expanded workbook exceeds the safe processing limit.")
            if any(item.flag_bits & 1 or item.file_size > 16 * 1024 * 1024 for item in entries):
                raise HTTPException(422, "Encrypted or oversized workbook entries are not supported.")
            if "[Content_Types].xml" not in archive.namelist():
                raise BadZipFile()
    except BadZipFile:
        raise HTTPException(422, "Upload a valid XLS or XLSX workbook.") from None
