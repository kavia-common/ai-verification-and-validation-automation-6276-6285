import os
import json
from flask import request, current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from werkzeug.utils import secure_filename

from ..utils import generate_id, utc_now_iso
from ..services.storage import Storage

blp = Blueprint(
    "SRS",
    "srs",
    url_prefix="/api",
    description="Upload SRS CSV and manage jobs",
)

ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@blp.route("/srs/upload")
class SRSUpload(MethodView):
    """Handle SRS CSV uploads and create a job context."""

    def post(self):
        """
        Upload SRS CSV (multipart/form-data) and create a job.
        Returns: { jobId, filename }
        """
        if "file" not in request.files:
            return {"error": "No file part"}, 400
        file = request.files["file"]
        if file.filename == "":
            return {"error": "No selected file"}, 400

        if not allowed_file(file.filename):
            return {"error": "Only .csv files are allowed"}, 400

        # Sanitize filename
        filename = secure_filename(file.filename)
        job_id = generate_id(prefix="job_")
        storage = Storage()

        # Save SRS into input directory namespaced by jobId
        input_dir = storage.get_job_input_dir(job_id)
        os.makedirs(input_dir, exist_ok=True)
        file_path = os.path.join(input_dir, filename)

        # Safety: ensure within input_dir
        file_path = storage.safe_join(input_dir, filename)
        file.save(file_path)

        # Create initial job metadata
        job_meta = {
            "id": job_id,
            "created_at": utc_now_iso(),
            "status": "uploaded",
            "srs": {"filename": filename, "path": file_path},
            "paths": {
                "input": input_dir,
                "cases_json": storage.get_job_cases_path(job_id),
                "tests_dir": storage.get_job_tests_dir(job_id),
            },
        }
        storage.save_job_metadata(job_id, job_meta)

        return {"jobId": job_id, "filename": filename}, 200


@blp.route("/jobs/<string:job_id>")
class JobDetails(MethodView):
    """Retrieve job metadata."""

    def get(self, job_id: str):
        """
        Get job metadata including SRS path, generated cases, and scripts.
        """
        storage = Storage()
        meta = storage.load_job_metadata(job_id)
        if not meta:
            return {"error": "Job not found"}, 404
        return meta, 200
