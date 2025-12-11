import json
import os
from typing import Any, Dict, List, Optional
from flask import current_app


class Storage:
    """Filesystem-based storage helper for jobs, runs, and reports."""

    def __init__(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.base_dir = base
        self.input_dir = os.path.join(base, "input")
        self.codebase_dir = os.path.join(base, "codebase")
        self.runs_dir = os.path.join(base, "runs")
        self.reports_dir = os.path.join(base, "reports")
        # Namespaces
        self.jobs_meta_dir = os.path.join(self.base_dir, "jobs")
        os.makedirs(self.jobs_meta_dir, exist_ok=True)
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.codebase_dir, exist_ok=True)
        os.makedirs(self.runs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    # PUBLIC_INTERFACE
    def safe_join(self, directory: str, filename: str) -> str:
        """Safely join a directory and a filename to prevent path traversal."""
        # Normalize and ensure directory is absolute
        directory = os.path.abspath(directory)
        path = os.path.abspath(os.path.join(directory, filename))
        if not path.startswith(directory + os.sep) and path != directory:
            raise ValueError("Invalid path")
        return path

    # --- Job paths and metadata ---

    def get_job_input_dir(self, job_id: str) -> str:
        d = os.path.join(self.input_dir, job_id)
        os.makedirs(d, exist_ok=True)
        return d

    def get_job_cases_path(self, job_id: str) -> str:
        d = os.path.join(self.codebase_dir, "test-cases")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{job_id}.json")

    def get_job_tests_dir(self, job_id: str) -> str:
        d = os.path.join(self.codebase_dir, "tests", job_id)
        os.makedirs(d, exist_ok=True)
        return d

    def get_job_meta_path(self, job_id: str) -> str:
        return os.path.join(self.jobs_meta_dir, f"{job_id}.json")

    def save_job_metadata(self, job_id: str, meta: Dict[str, Any]) -> None:
        with open(self.get_job_meta_path(job_id), "w") as f:
            json.dump(meta, f, indent=2)

    def load_job_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        path = self.get_job_meta_path(job_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    # --- Run paths and metadata ---

    def get_run_dir(self, run_id: str) -> str:
        d = os.path.join(self.runs_dir, run_id)
        os.makedirs(d, exist_ok=True)
        return d

    def get_run_artifacts_dir(self, run_id: str) -> str:
        d = os.path.join(self.get_run_dir(run_id), "artifacts")
        os.makedirs(d, exist_ok=True)
        return d

    def get_run_meta_path(self, run_id: str) -> str:
        return os.path.join(self.get_run_dir(run_id), "run.json")

    def get_report_json_path(self, run_id: str) -> str:
        return os.path.join(self.reports_dir, f"{run_id}.json")

    def get_report_html_path(self, run_id: str) -> str:
        return os.path.join(self.reports_dir, f"{run_id}.html")

    def save_run_metadata(self, run_id: str, meta: Dict[str, Any]) -> None:
        with open(self.get_run_meta_path(run_id), "w") as f:
            json.dump(meta, f, indent=2)

    def load_run_metadata(self, run_id: str) -> Optional[Dict[str, Any]]:
        path = self.get_run_meta_path(run_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def save_report(self, run_id: str, report: Dict[str, Any]) -> None:
        with open(self.get_report_json_path(run_id), "w") as f:
            json.dump(report, f, indent=2)

    def load_report(self, run_id: str) -> Optional[Dict[str, Any]]:
        path = self.get_report_json_path(run_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    # PUBLIC_INTERFACE
    def list_runs(self) -> List[Dict[str, Any]]:
        """List runs with summarized metadata for quick listing."""
        runs = []
        if not os.path.exists(self.runs_dir):
            return runs
        for run_id in sorted(os.listdir(self.runs_dir)):
            meta = self.load_run_metadata(run_id)
            if not meta:
                continue
            report = self.load_report(run_id) or {}
            totals = report.get("totals") or meta.get("totals") or {}
            runs.append(
                {
                    "runId": run_id,
                    "jobId": meta.get("jobId"),
                    "status": meta.get("status"),
                    "timestamp": meta.get("created_at"),
                    "duration": meta.get("duration"),
                    "totals": totals,
                    "passed": totals.get("passed"),
                    "failed": totals.get("failed"),
                }
            )
        return runs
