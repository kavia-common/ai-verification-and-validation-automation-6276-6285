from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

from ..services.test_case_creation import generate_test_cases_for_job
from ..services.test_script_creation import generate_test_scripts_for_job
from ..services.storage import Storage

blp = Blueprint(
    "Generation",
    "generation",
    url_prefix="/api/generate",
    description="Generation of test cases and test scripts",
)


@blp.route("/test-cases")
class GenerateTestCases(MethodView):
    """Generate test cases from an uploaded SRS CSV using LLM or Mock provider."""

    def post(self):
        """
        Body: { jobId }
        Returns: { jobId, casesPath, count }
        """
        data = request.get_json(silent=True) or {}
        job_id = data.get("jobId")
        if not job_id:
            return {"error": "jobId is required"}, 400

        result = generate_test_cases_for_job(job_id)
        if "error" in result:
            return result, 400
        return result, 200


@blp.route("/test-scripts")
class GenerateTestScripts(MethodView):
    """Generate pytest/Playwright test scripts from previously generated cases."""

    def post(self):
        """
        Body: { jobId }
        Returns: { jobId, testsPath, files }
        """
        data = request.get_json(silent=True) or {}
        job_id = data.get("jobId")
        if not job_id:
            return {"error": "jobId is required"}, 400

        result = generate_test_scripts_for_job(job_id)
        if "error" in result:
            return result, 400
        return result, 200
