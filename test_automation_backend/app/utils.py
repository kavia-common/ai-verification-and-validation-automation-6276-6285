import csv
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


# PUBLIC_INTERFACE
def generate_id(prefix: str = "") -> str:
    """Generate a unique id with optional prefix using uuid4."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# PUBLIC_INTERFACE
def utc_now_iso() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


# PUBLIC_INTERFACE
def parse_csv_flex(path: str) -> List[Dict[str, Any]]:
    """Parse CSV file into a list of dicts, handling varied schemas gracefully."""
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for r in reader:
            # Normalize keys to lowercase
            norm = {str(k).strip().lower(): v for k, v in r.items()}
            rows.append(norm)
    return rows


# PUBLIC_INTERFACE
def sanitize_identifier(text: str) -> str:
    """Sanitize a string to be a valid python identifier-ish for filenames and test names."""
    if not text:
        return "item"
    allowed = []
    for ch in text:
        if ch.isalnum() or ch in ("_", "-"):
            allowed.append(ch.lower())
        else:
            allowed.append("_")
    s = "".join(allowed).strip("_")
    return s or "item"
