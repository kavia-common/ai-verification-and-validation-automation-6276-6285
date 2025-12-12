import csv
import hashlib
import io
import os
import time
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Tuple


REQUIRED_SRS_COLUMNS = ["requirement_id", "title", "description", "priority"]


@dataclass
class CSVValidationResult:
    valid: bool
    errors: List[str]
    rows: List[Dict[str, str]]


def secure_filename_like(name: str) -> str:
    """
    Create a safe filename-ish string without importing extra deps.
    """
    keep = "-_.() "
    sanitized = "".join(c for c in name if c.isalnum() or c in keep)
    sanitized = "_".join(sanitized.split())
    return sanitized or f"file_{int(time.time())}"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def validate_srs_csv(file_bytes: bytes) -> CSVValidationResult:
    """
    Validate CSV content against required columns and basic data presence.
    Returns CSVValidationResult with parsed rows.
    """
    errors: List[str] = []
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("utf-8")
        except Exception:
            return CSVValidationResult(False, ["Invalid encoding; expected UTF-8."], [])

    f = io.StringIO(text)
    try:
        reader = csv.DictReader(f)
    except csv.Error as e:
        return CSVValidationResult(False, [f"CSV parse error: {e}"], [])

    header = [h.strip() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED_SRS_COLUMNS if c not in header]
    if missing:
        return CSVValidationResult(False, [f"Missing required columns: {', '.join(missing)}"], [])

    rows: List[Dict[str, str]] = []
    for idx, row in enumerate(reader, start=2):
        # Normalize keys
        normalized = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        # Basic non-empty checks
        for col in REQUIRED_SRS_COLUMNS:
            if not normalized.get(col):
                errors.append(f"Row {idx}: '{col}' is empty.")
        rows.append(normalized)

    return CSVValidationResult(valid=len(errors) == 0, errors=errors, rows=rows)


def write_zip_from_files(files: List[Tuple[str, bytes]]) -> bytes:
    """
    Create a zip archive from a list of (arcname, content_bytes).
    """
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, content in files:
            z.writestr(arcname, content)
    return bio.getvalue()
