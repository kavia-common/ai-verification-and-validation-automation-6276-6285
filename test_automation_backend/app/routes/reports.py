import os
from flask import send_file
from flask.views import MethodView
from flask_smorest import Blueprint

from ..services.storage import Storage

blp = Blueprint(
    "Reports",
    "reports",
    url_prefix="/api",
    description="Run listing, report retrieval, and artifacts",
)


@blp.route("/runs")
class Runs(MethodView):
    """List all runs with basic metadata and totals."""

    def get(self):
        storage = Storage()
        runs = storage.list_runs()
        return runs, 200


@blp.route("/runs/<string:run_id>")
class RunDetails(MethodView):
    """Get run metadata and available links."""

    def get(self, run_id: str):
        storage = Storage()
        meta = storage.load_run_metadata(run_id)
        if not meta:
            return {"error": "Run not found"}, 404
        return meta, 200


@blp.route("/runs/<string:run_id>/report")
class RunReport(MethodView):
    """Get run aggregated report JSON."""

    def get(self, run_id: str):
        storage = Storage()
        report = storage.load_report(run_id)
        if not report:
            return {"error": "Report not found"}, 404
        return report, 200


@blp.route("/runs/<string:run_id>/report.html")
class RunReportHTML(MethodView):
    """Optional HTML report if available, otherwise 404."""

    def get(self, run_id: str):
        storage = Storage()
        html_path = storage.get_report_html_path(run_id)
        if os.path.exists(html_path):
            return send_file(html_path, mimetype="text/html")
        return {"error": "HTML report not available"}, 404


@blp.route("/runs/<string:run_id>/artifacts/<path:filename>")
class RunArtifact(MethodView):
    """Serve an artifact file from the run's artifact directory."""

    def get(self, run_id: str, filename: str):
        storage = Storage()
        artifacts_dir = storage.get_run_artifacts_dir(run_id)
        safe_path = storage.safe_join(artifacts_dir, filename)
        if not os.path.exists(safe_path):
            return {"error": "Artifact not found"}, 404
        return send_file(safe_path)
