import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .extensions import db
from .models import SRS, SRSVersion, TestCase, TestScript, TestRun, TestResult, Artifact
from .utils import ensure_dir, secure_filename_like, sha256_bytes, validate_srs_csv, write_zip_from_files
from .errors import ApiError


def _storage_root() -> str:
    # Persist artifacts under instance/storage to avoid container FS issues.
    root = os.path.join(os.getcwd(), "instance", "storage")
    ensure_dir(root)
    return root


class SRSService:
    """
    Service for storing, validating and versioning SRS CSV uploads.
    """

    # PUBLIC_INTERFACE
    @staticmethod
    def upload_srs(name: str, uploaded_by: Optional[str], file_bytes: bytes, notes: Optional[str] = None) -> Tuple[SRS, SRSVersion, List[Dict[str, str]]]:
        """Validate and store an SRS CSV file as a new version; returns SRS entity, created SRSVersion, and parsed rows."""
        result = validate_srs_csv(file_bytes)
        if not result.valid:
            raise ApiError(400, "Invalid SRS CSV", errors={"validation": result.errors})

        # Upsert SRS by name (case sensitive)
        srs = db.session.query(SRS).filter_by(name=name, is_active=True).one_or_none()
        if not srs:
            srs = SRS(name=name, uploaded_by=uploaded_by, description=None)
            db.session.add(srs)
            db.session.flush()

        # Determine next version number
        latest_version = db.session.query(SRSVersion).filter_by(srs_id=srs.id).order_by(SRSVersion.version.desc()).first()
        next_ver = (latest_version.version + 1) if latest_version else 1

        # Store file on disk
        srs_dir = os.path.join(_storage_root(), "srs", f"{srs.id}")
        ensure_dir(srs_dir)
        safe_name = secure_filename_like(f"{name}_v{next_ver}.csv")
        storage_path = os.path.join(srs_dir, safe_name)
        with open(storage_path, "wb") as f:
            f.write(file_bytes)
        checksum = sha256_bytes(file_bytes)

        srs_ver = SRSVersion(
            srs_id=srs.id,
            version=next_ver,
            filename=safe_name,
            storage_path=storage_path,
            file_hash=checksum,
            notes=notes,
        )
        db.session.add(srs_ver)
        db.session.commit()

        return srs, srs_ver, result.rows

    # PUBLIC_INTERFACE
    @staticmethod
    def list_srs() -> List[SRS]:
        """List active SRS documents."""
        return db.session.query(SRS).filter_by(is_active=True).all()

    # PUBLIC_INTERFACE
    @staticmethod
    def list_versions(srs_id: int) -> List[SRSVersion]:
        """List versions for a specific SRS."""
        srs = db.session.get(SRS, srs_id)
        if not srs or not srs.is_active:
            raise ApiError(404, "SRS not found")
        return db.session.query(SRSVersion).filter_by(srs_id=srs_id).order_by(SRSVersion.version.asc()).all()


class LLMService:
    """
    Mockable LLM service for test case and script generation.
    """

    @staticmethod
    def is_mock() -> bool:
        return os.getenv("MOCK_LLM", "true").lower() in ("1", "true", "yes")

    # PUBLIC_INTERFACE
    @staticmethod
    def generate_test_cases(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate test cases from SRS rows. In mock mode, synthesize simple test cases."""
        if LLMService.is_mock():
            cases = []
            for r in rows:
                rid = r.get("requirement_id") or "REQ"
                title = r.get("title") or f"Test for {rid}"
                desc = r.get("description") or ""
                prio = r.get("priority") or "Medium"
                cases.append({
                    "requirement_id": rid,
                    "title": f"[AUTO] {title}",
                    "description": f"Generated test for requirement {rid}. {desc}",
                    "priority": prio,
                })
            return cases
        # Placeholder for real LLM call integration.
        raise ApiError(501, "LLM generation not implemented; enable MOCK_LLM=true for mock mode.")


class ScriptService:
    """
    Generate pytest + Playwright test scripts from approved test cases.
    """

    # PUBLIC_INTERFACE
    @staticmethod
    def generate_pytest_playwright_script(test_case: TestCase) -> Tuple[str, str]:
        """Return (filename, code) for a pytest Playwright script representing a test case."""
        func_name = f"test_{test_case.requirement_id.lower().replace('-', '_').replace(' ', '_')}"
        filename = f"{func_name}.py"
        # Minimal playwright page usage in mock template (no external dependency is executed in mock)
        code = f'''"""
Auto-generated test script for requirement {test_case.requirement_id}
Title: {test_case.title}
"""

import pytest

# NOTE: This mock template does not import playwright to keep runtime light.
# In a real environment, you would: from playwright.sync_api import sync_playwright

@pytest.mark.requirement("{test_case.requirement_id}")
def {func_name}():
    """
    Validate requirement: {test_case.requirement_id}
    Description: {test_case.description or ""}
    """
    # MOCK: Replace with real Playwright steps.
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=True)
    #     page = browser.new_page()
    #     page.goto("https://example.com")
    #     assert page.title()
    #     browser.close()
    assert True
'''
        return filename, code

    # PUBLIC_INTERFACE
    @staticmethod
    def create_scripts_for_cases(cases: List[TestCase], actor: Optional[str]) -> List[TestScript]:
        """Generate and persist scripts for cases; returns created TestScript entities."""
        created: List[TestScript] = []
        for c in cases:
            filename, code = ScriptService.generate_pytest_playwright_script(c)
            script = TestScript(
                test_case_id=c.id,
                language="python",
                framework="pytest-playwright",
                filename=filename,
                code=code,
                last_generated_by=actor,
                gen_metadata={"template": "mock", "ts": datetime.utcnow().isoformat()},
            )
            db.session.add(script)
            created.append(script)
        db.session.commit()
        return created


class ExecutionService:
    """
    Orchestrate test execution using pytest. Supports MOCK execution without running external tools.
    """

    @staticmethod
    def is_mock() -> bool:
        return os.getenv("MOCK_EXECUTION", "true").lower() in ("1", "true", "yes")

    # PUBLIC_INTERFACE
    @staticmethod
    def trigger_run(selected_test_case_ids: Optional[List[int]], triggered_by: Optional[str], params: Optional[Dict] = None) -> TestRun:
        """Create a TestRun and start execution (mock immediate completion)."""
        run = TestRun(
            triggered_by=triggered_by,
            status="queued",
            run_params=params or {},
            started_at=None,
            finished_at=None,
        )
        db.session.add(run)
        db.session.flush()

        # Select cases
        q = db.session.query(TestCase).filter_by(is_active=True)
        if selected_test_case_ids:
            q = q.filter(TestCase.id.in_(selected_test_case_ids))
        cases = q.all()

        # Create pending results
        for c in cases:
            res = TestResult(test_run_id=run.id, test_case_id=c.id, status="pending")
            db.session.add(res)
        db.session.commit()

        # For simplicity, immediately execute synchronously (mock) to update status/results
        if ExecutionService.is_mock():
            ExecutionService._complete_run_mock(run)
        else:
            ExecutionService._run_with_pytest(run, cases)

        return db.session.get(TestRun, run.id)

    @staticmethod
    def _complete_run_mock(run: TestRun) -> None:
        run.status = "running"
        run.started_at = datetime.utcnow()
        db.session.commit()

        # Mark all results as passed with mock durations
        results = db.session.query(TestResult).filter_by(test_run_id=run.id).all()
        for idx, r in enumerate(results, 1):
            r.status = "passed"
            r.duration_seconds = 0.1 * idx
            r.error_message = None
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def _run_with_pytest(run: TestRun, cases: List[TestCase]) -> None:
        """
        Real execution path using pytest. Writes scripts to a temp dir and runs pytest.
        This will likely require pytest/playwright runtime in container; use mock for CI safety.
        """
        run.status = "running"
        run.started_at = datetime.utcnow()
        db.session.commit()

        tempdir = tempfile.mkdtemp(prefix=f"testrun_{run.id}_")
        files: List[Tuple[str, bytes]] = []

        # Dump scripts to files
        for c in cases:
            scripts = db.session.query(TestScript).filter_by(test_case_id=c.id, is_active=True).all()
            if not scripts:
                # create default script if missing
                fname, code = ScriptService.generate_pytest_playwright_script(c)
                files.append((fname, code.encode("utf-8")))
            else:
                for s in scripts:
                    files.append((s.filename, s.code.encode("utf-8")))

        # Write files to tempdir
        for fname, content in files:
            path = os.path.join(tempdir, fname)
            with open(path, "wb") as f:
                f.write(content)

        # Run pytest
        try:
            proc = subprocess.run(
                ["pytest", "-q", tempdir],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300,
            )
            output = proc.stdout
            passed = proc.returncode == 0
        except Exception as e:
            output = f"Execution error: {e}"
            passed = False

        # Update results crudely based on return code (for demo)
        results = db.session.query(TestResult).filter_by(test_run_id=run.id).all()
        for r in results:
            r.status = "passed" if passed else "failed"
            r.duration_seconds = 0.5
            r.error_message = None if passed else "Pytest reported failures"
            # Save logs as artifact
        # Save run-level log artifact
        art_dir = os.path.join(_storage_root(), "runs", f"{run.id}")
        ensure_dir(art_dir)
        log_path = os.path.join(art_dir, "pytest_output.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
        artifact = Artifact(test_run_id=run.id, kind="log", filename="pytest_output.txt", storage_path=log_path)
        db.session.add(artifact)

        run.status = "completed" if passed else "failed"
        run.finished_at = datetime.utcnow()
        db.session.commit()


class ResultsService:
    """
    Retrieval and export helpers for scripts and results.
    """

    # PUBLIC_INTERFACE
    @staticmethod
    def get_run(run_id: int) -> TestRun:
        """Fetch a TestRun by id or 404."""
        run = db.session.get(TestRun, run_id)
        if not run or not run.is_active:
            raise ApiError(404, "TestRun not found")
        return run

    # PUBLIC_INTERFACE
    @staticmethod
    def get_run_results(run_id: int) -> List[TestResult]:
        """List results for a run."""
        ResultsService.get_run(run_id)
        return db.session.query(TestResult).filter_by(test_run_id=run_id).all()

    # PUBLIC_INTERFACE
    @staticmethod
    def export_scripts_zip(srs_version_id: int) -> Tuple[str, bytes]:
        """Bundle scripts associated with an SRSVersion into a zip archive."""
        cases = db.session.query(TestCase).filter_by(srs_version_id=srs_version_id, is_active=True).all()
        files: List[Tuple[str, bytes]] = []
        for c in cases:
            scripts = db.session.query(TestScript).filter_by(test_case_id=c.id, is_active=True).all()
            for s in scripts:
                files.append((s.filename, s.code.encode("utf-8")))
        if not files:
            raise ApiError(404, "No scripts found for this SRS version")
        blob = write_zip_from_files(files)
        fname = f"srs_version_{srs_version_id}_scripts.zip"
        return fname, blob

    # PUBLIC_INTERFACE
    @staticmethod
    def export_results_csv(run_id: int) -> Tuple[str, bytes]:
        """Export results of a run as a CSV."""
        results = ResultsService.get_run_results(run_id)
        headers = ["test_result_id", "test_case_id", "status", "duration_seconds", "error_message"]
        lines = [",".join(headers)]
        for r in results:
            fields = [
                str(r.id),
                str(r.test_case_id or ""),
                r.status,
                str(r.duration_seconds or ""),
                '"' + (r.error_message or "").replace('"', '""') + '"',
            ]
            lines.append(",".join(fields))
        content = ("\n".join(lines)).encode("utf-8")
        return f"run_{run_id}_results.csv", content


class GenerationService:
    """
    High-level orchestration: from SRSVersion rows to TestCase records and TestScript creation.
    """

    # PUBLIC_INTERFACE
    @staticmethod
    def generate_test_cases_for_version(srs_version_id: int) -> List[TestCase]:
        """Invoke LLM to create test cases and persist them."""
        srs_version = db.session.get(SRSVersion, srs_version_id)
        if not srs_version or not srs_version.is_active:
            raise ApiError(404, "SRSVersion not found")

        # Load CSV bytes
        try:
            with open(srs_version.storage_path, "rb") as f:
                csv_bytes = f.read()
        except FileNotFoundError:
            raise ApiError(500, "Stored CSV file is missing")

        val = validate_srs_csv(csv_bytes)
        if not val.valid:
            raise ApiError(400, "Stored CSV no longer validates", errors={"validation": val.errors})

        generated = LLMService.generate_test_cases(val.rows)
        created: List[TestCase] = []
        for g in generated:
            case = TestCase(
                srs_version_id=srs_version.id,
                requirement_id=g["requirement_id"],
                title=g["title"],
                description=g.get("description"),
                priority=g.get("priority"),
                status="generated",
                metadata={"source": "llm_mock" if LLMService.is_mock() else "llm"},
            )
            db.session.add(case)
            created.append(case)
        db.session.commit()
        return created

    # PUBLIC_INTERFACE
    @staticmethod
    def generate_scripts_for_version(srs_version_id: int, actor: Optional[str]) -> List[TestScript]:
        """Create scripts for all active cases of an SRSVersion."""
        cases = db.session.query(TestCase).filter_by(srs_version_id=srs_version_id, is_active=True).all()
        if not cases:
            raise ApiError(404, "No test cases found for this SRSVersion")
        return ScriptService.create_scripts_for_cases(cases, actor)
