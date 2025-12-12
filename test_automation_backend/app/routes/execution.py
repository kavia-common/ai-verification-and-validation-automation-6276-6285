from flask import make_response
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from ..services import ExecutionService, ResultsService


blp = Blueprint(
    "Execution",
    "execution",
    url_prefix="/execution",
    description="Trigger and monitor test execution runs",
)


class RunParams(Schema):
    triggered_by = fields.Str(required=False, allow_none=True, description="User initiating run")
    test_case_ids = fields.List(fields.Int(), required=False, allow_none=True, description="Subset of TestCase IDs to execute")
    params = fields.Dict(required=False, allow_none=True, description="Execution parameters")


@blp.route("/runs", methods=["POST"])
class TriggerRun(MethodView):
    """Create a TestRun and start execution (mock immediate for CI)."""
    @blp.arguments(RunParams)
    @blp.response(201)
    def post(self, args):
        run = ExecutionService.trigger_run(
            selected_test_case_ids=args.get("test_case_ids"),
            triggered_by=args.get("triggered_by"),
            params=args.get("params"),
        )
        return {
            "id": run.id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }


@blp.route("/runs/<int:run_id>", methods=["GET"])
class RunStatus(MethodView):
    """Fetch status of a specific run."""
    @blp.response(200)
    def get(self, run_id: int):
        run = ResultsService.get_run(run_id)
        return {
            "id": run.id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }


@blp.route("/runs/<int:run_id>/results", methods=["GET"])
class RunResults(MethodView):
    """List results for a run."""
    @blp.response(200)
    def get(self, run_id: int):
        results = ResultsService.get_run_results(run_id)
        return {
            "items": [
                {
                    "id": r.id,
                    "test_case_id": r.test_case_id,
                    "status": r.status,
                    "duration_seconds": r.duration_seconds,
                    "error_message": r.error_message,
                }
                for r in results
            ]
        }


@blp.route("/runs/<int:run_id>/export.csv", methods=["GET"])
class ExportResultsCSV(MethodView):
    """Download results of a run as CSV."""
    def get(self, run_id: int):
        fname, blob = ResultsService.export_results_csv(run_id)
        resp = make_response(blob)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = f'attachment; filename="{fname}"'
        return resp


scripts_blp = Blueprint(
    "Scripts",
    "scripts",
    url_prefix="/scripts",
    description="Download generated test scripts",
)


@scripts_blp.route("/versions/<int:version_id>/export.zip", methods=["GET"])
class ExportScriptsZip(MethodView):
    """Download all generated scripts for a version as a ZIP archive."""
    def get(self, version_id: int):
        fname, blob = ResultsService.export_scripts_zip(version_id)
        resp = make_response(blob)
        resp.headers["Content-Type"] = "application/zip"
        resp.headers["Content-Disposition"] = f'attachment; filename="{fname}"'
        return resp
