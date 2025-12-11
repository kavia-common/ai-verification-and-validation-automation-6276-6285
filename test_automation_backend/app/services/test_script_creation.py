import json
import os
from typing import Any, Dict, List

from ..utils import utc_now_iso, sanitize_identifier
from .storage import Storage


def _load_cases(storage: Storage, job_id: str) -> List[Dict[str, Any]]:
    path = storage.get_job_cases_path(job_id)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("test_cases") or []


def _write_conftest(tests_dir: str) -> None:
    conftest = """# Minimal Playwright/pytest fixtures
import pytest

@pytest.fixture(scope="session")
def browser_type_launch_args():
    # Ensure headless; users can override via CLI if needed
    return {"headless": True}
"""
    with open(os.path.join(tests_dir, "conftest.py"), "w") as f:
        f.write(conftest)


def _render_test_file(requirement_id: str, cases: List[Dict[str, Any]]) -> str:
    lines = [
        "import pytest",
        "from typing import List",
        "",
        "",
    ]
    for idx, c in enumerate(cases, start=1):
        test_fn = f"test_{sanitize_identifier(requirement_id)}_{idx}"
        title = c.get("title") or "Untitled"
        steps = c.get("steps") or []
        expected = c.get("expected") or ""
        # Keep it simple and not dependent on actual app URLs
        body = [
            f"def {test_fn}():",
            f"    \"\"\"{title}\"\"\"",
            "    steps: List[str] = " + repr(steps),
            "    expected = " + repr(expected),
            "    # Placeholder test - replace with real Playwright actions.",
            "    assert isinstance(steps, list)",
            "    assert expected is not None",
            "",
        ]
        lines.extend(body)
    return "\n".join(lines)


# PUBLIC_INTERFACE
def generate_test_scripts_for_job(job_id: str) -> Dict[str, Any]:
    """Generate pytest test scripts from previously generated test cases."""
    storage = Storage()
    job_meta = storage.load_job_metadata(job_id)
    if not job_meta:
        return {"error": "Job not found"}
    cases = _load_cases(storage, job_id)
    if not cases:
        return {"error": "No cases found; generate test cases first"}

    tests_dir = storage.get_job_tests_dir(job_id)
    os.makedirs(tests_dir, exist_ok=True)
    _write_conftest(tests_dir)

    # Group tests by requirement id prefix
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for c in cases:
        rid = str(c.get("id") or "REQ")
        buckets.setdefault(rid, []).append(c)

    written_files: List[str] = []
    for rid, group in buckets.items():
        fname = f"test_{sanitize_identifier(rid)}.py"
        fpath = os.path.join(tests_dir, fname)
        content = _render_test_file(rid, group)
        with open(fpath, "w") as f:
            f.write(content)
        written_files.append(fpath)

    # Update job metadata
    job_meta["status"] = "scripts_generated"
    job_meta["paths"]["tests_dir"] = tests_dir
    job_meta["test_files"] = written_files
    job_meta["scripts_generated_at"] = utc_now_iso()
    job_meta["scripts_count"] = len(written_files)
    storage.save_job_metadata(job_id, job_meta)

    return {"jobId": job_id, "testsPath": tests_dir, "files": [os.path.basename(p) for p in written_files]}
