from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from ..services import SRSService, GenerationService
from ..errors import ApiError


blp = Blueprint(
    "SRS",
    "srs",
    url_prefix="/srs",
    description="Upload and manage SRS CSV files with validation and versioning",
)


class UploadParams(Schema):
    name = fields.Str(required=True, description="Logical SRS name")
    uploaded_by = fields.Str(required=False, allow_none=True, description="Uploader identity")
    notes = fields.Str(required=False, allow_none=True, description="Upload notes")


@blp.route("/", methods=["GET"])
class SRSList(MethodView):
    """List active SRS entries."""
    @blp.response(200)
    def get(self):
        items = SRSService.list_srs()
        return {
            "items": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "uploaded_by": s.uploaded_by,
                    "created_at": s.created_at.isoformat(),
                }
                for s in items
            ]
        }


@blp.route("/upload", methods=["POST"])
class SRSUpload(MethodView):
    """Upload a new SRS CSV; creates a new SRS or appends a version if name exists."""
    @blp.arguments(UploadParams, location="form")
    @blp.response(201)
    def post(self, args):
        """
        Expects multipart/form-data with fields:
        - name (str) logical SRS name
        - uploaded_by (optional str)
        - notes (optional str)
        - file (file) CSV file
        """
        file = request.files.get("file")
        if not file:
            raise ApiError(400, "Missing file in 'file' field")
        file_bytes = file.read()
        srs, version, rows = SRSService.upload_srs(
            name=args["name"],
            uploaded_by=args.get("uploaded_by"),
            file_bytes=file_bytes,
            notes=args.get("notes"),
        )
        return {
            "srs": {"id": srs.id, "name": srs.name},
            "version": {"id": version.id, "version": version.version, "filename": version.filename},
            "stats": {"row_count": len(rows)},
        }


@blp.route("/<int:srs_id>/versions", methods=["GET"])
class SRSVersions(MethodView):
    """List versions for a given SRS id."""
    @blp.response(200)
    def get(self, srs_id: int):
        versions = SRSService.list_versions(srs_id)
        return {
            "items": [
                {
                    "id": v.id,
                    "version": v.version,
                    "filename": v.filename,
                    "created_at": v.created_at.isoformat(),
                    "notes": v.notes,
                }
                for v in versions
            ]
        }


class GenParams(Schema):
    actor = fields.Str(required=False, allow_none=True, description="User initiating generation")


@blp.route("/versions/<int:version_id>/generate-cases", methods=["POST"])
class GenerateCases(MethodView):
    """Trigger LLM to generate test cases for an SRS version."""
    @blp.response(201)
    def post(self, version_id: int):
        created = GenerationService.generate_test_cases_for_version(version_id)
        return {
            "created": [
                {
                    "id": c.id,
                    "requirement_id": c.requirement_id,
                    "title": c.title,
                    "status": c.status,
                    "priority": c.priority,
                }
                for c in created
            ],
            "count": len(created),
        }


@blp.route("/versions/<int:version_id>/generate-scripts", methods=["POST"])
class GenerateScripts(MethodView):
    """Generate pytest+Playwright scripts for all test cases in a version."""
    @blp.arguments(GenParams)
    @blp.response(201)
    def post(self, args, version_id: int):
        actor = args.get("actor")
        created = GenerationService.generate_scripts_for_version(version_id, actor)
        return {
            "created": [
                {
                    "id": s.id,
                    "filename": s.filename,
                    "framework": s.framework,
                    "language": s.language,
                }
                for s in created
            ],
            "count": len(created),
        }
