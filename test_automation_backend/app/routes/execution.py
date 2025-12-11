from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

from ..services.test_script_execution import execute_tests_for_job

blp = Blueprint(
    "Execution",
    "execution",
    url_prefix="/api",
    description="Execute generated tests",
)


@blp.route("/execute")
class Execute(MethodView):
    """Execute pytest for a given job and create a run/report."""

    def post(self):
        """
        Body: { jobId }
        Returns: { runId, jobId, status, totals }
        """
        data = request.get_json(silent=True) or {}
        job_id = data.get("jobId")
        if not job_id:
            return {"error": "jobId is required"}, 400
        result = execute_tests_for_job(job_id)
        status_code = 200 if "runId" in result else 400
        return result, status_code
