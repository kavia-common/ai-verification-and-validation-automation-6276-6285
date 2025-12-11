import json
import os
import subprocess
import time
from typing import Any, Dict, List

from ..utils import generate_id, utc_now_iso
from .storage import Storage


def _aggregate_pytest_output(junit_xml_path: str) -> Dict[str, Any]:
    # Minimal parser-free approach: summarize based on file existence and return code is handled separately.
    # For richer details, we could parse XML, but keep lightweight for now.
    if not os.path.exists(junit_xml_path):
        return {"total": 0, "passed": 0, "failed": 0}
    # Primitive parse: count occurrences (not robust but avoids extra deps)
    try:
        with open(junit_xml_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        total = content.count("<testcase ")
        failed = content.count("<failure ") + content.count("<error ")
        skipped = content.count("<skipped ")
        passed = max(total - failed - skipped, 0)
        return {"total": total, "passed": passed, "failed": failed, "skipped": skipped}
    except Exception:
        return {"total": 0, "passed": 0, "failed": 0}


# PUBLIC_INTERFACE
def execute_tests_for_job(job_id: str) -> Dict[str, Any]:
    """Execute pytest for the job's generated tests and create a run/report result."""
    storage = Storage()
    job_meta = storage.load_job_metadata(job_id)
    if not job_meta:
        return {"error": "Job not found"}
    tests_dir = job_meta.get("paths", {}).get("tests_dir") or storage.get_job_tests_dir(job_id)
    if not os.path.exists(tests_dir):
        return {"error": "Tests not found; generate test scripts first"}

    run_id = generate_id(prefix="run_")
    run_dir = storage.get_run_dir(run_id)
    artifacts_dir = storage.get_run_artifacts_dir(run_id)
    junit_xml_path = os.path.join(artifacts_dir, "junit.xml")

    # Prepare environment for headless execution
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Execute pytest in subprocess
    start = time.time()
    cmd = [
        "pytest",
        tests_dir,
        "-q",
        f"--junitxml={junit_xml_path}",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60 * 5,  # 5 minutes safety
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        status = "passed" if rc == 0 else "failed"
    except FileNotFoundError:
        # pytest is missing
        rc = 1
        stdout = ""
        stderr = "pytest not found in environment"
        status = "error"
    except subprocess.TimeoutExpired as e:
        rc = 1
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + "\nTimeoutExpired"
        status = "timeout"

    duration = time.time() - start

    # Persist artifacts
    with open(os.path.join(artifacts_dir, "stdout.txt"), "w") as f:
        f.write(stdout or "")
    with open(os.path.join(artifacts_dir, "stderr.txt"), "w") as f:
        f.write(stderr or "")

    # Aggregate simple report
    totals = _aggregate_pytest_output(junit_xml_path)
    report: Dict[str, Any] = {
        "runId": run_id,
        "jobId": job_id,
        "created_at": utc_now_iso(),
        "duration": duration,
        "status": status,
        "totals": {
            "total": totals.get("total", 0),
            "passed": totals.get("passed", 0),
            "failed": totals.get("failed", 0),
            "skipped": totals.get("skipped", 0),
        },
        "artifacts": {
            "junit_xml": "junit.xml" if os.path.exists(junit_xml_path) else None,
            "stdout": "stdout.txt",
            "stderr": "stderr.txt",
        },
    }
    storage.save_report(run_id, report)

    # Save run metadata
    run_meta = {
        "id": run_id,
        "jobId": job_id,
        "created_at": report["created_at"],
        "duration": duration,
        "status": status,
        "artifacts_dir": artifacts_dir,
        "totals": report["totals"],
        "paths": {
            "report_json": storage.get_report_json_path(run_id),
            "report_html": storage.get_report_html_path(run_id),
        },
        "return_code": rc,
    }
    storage.save_run_metadata(run_id, run_meta)

    return {"runId": run_id, "jobId": job_id, "status": status, "totals": report["totals"]}
