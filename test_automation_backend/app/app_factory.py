import os
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .config import get_config
from .extensions import db, ma
from .errors import register_error_handlers


def _ensure_instance_dir(app: Flask) -> None:
    """Ensure instance directory exists for SQLite file DBs."""
    instance_path = os.path.join(os.getcwd(), "instance")
    os.makedirs(instance_path, exist_ok=True)
    app.instance_path = instance_path  # for clarity


# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask application with DB, error handlers, blueprints and API docs."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Ensure instance dir for SQLite persistence
    _ensure_instance_dir(app)

    # Configure CORS: allow specific frontend origin if provided
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
    CORS(app, resources={r"/*": {"origins": frontend_origin}})

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    # API and docs
    api = Api(app)
    # Optional tags grouping for Swagger UI
    api.spec.components.security_schemes = {}
    api.spec.tags = [
        {"name": "Healt Check", "description": "Health check route"},
        {"name": "SRS", "description": "Upload and manage SRS CSV files"},
        {"name": "Execution", "description": "Trigger and monitor test runs"},
        {"name": "Scripts", "description": "Download generated scripts"},
    ]

    # Register blueprints
    from .routes.health import blp as health_blp
    from .routes.srs import blp as srs_blp
    from .routes.execution import blp as exec_blp, scripts_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(srs_blp)
    api.register_blueprint(exec_blp)
    api.register_blueprint(scripts_blp)

    # Error handlers
    register_error_handlers(app)

    # CLI: create-db for quick local setup
    @app.cli.command("create-db")
    def create_db():  # pragma: no cover
        """Create database tables using SQLAlchemy models (dev only)."""
        with app.app_context():
            db.create_all()
            print("Database tables created.")

    return app
