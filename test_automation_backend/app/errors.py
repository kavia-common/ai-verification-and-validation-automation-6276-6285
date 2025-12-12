from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from flask import jsonify


@dataclass
class ApiError(Exception):
    """
    Standardized API error exception. Raise this for consistent error responses.
    """
    code: int
    message: str
    status: str = "error"
    errors: Optional[Dict[str, Any]] = None

    def to_response(self) -> Tuple[Any, int]:
        payload = {
            "code": self.code,
            "status": self.status,
            "message": self.message,
        }
        if self.errors:
            payload["errors"] = self.errors
        return jsonify(payload), self.code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return err.to_response()

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"code": 404, "status": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(400)
    def handle_bad_request(_):
        return jsonify({"code": 400, "status": "bad_request", "message": "Bad request"}), 400

    @app.errorhandler(500)
    def handle_internal_error(err):
        return jsonify({
            "code": 500,
            "status": "internal_error",
            "message": "An unexpected error occurred",
            "errors": {"detail": str(err)}
        }), 500
