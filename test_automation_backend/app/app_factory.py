import os
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .config import get_config
from .extensions import db, ma


def _ensure_instance_dir(app: Flask) -> None:
    """Ensure instance directory exists for SQLite file DBs."""
    instance_path = os.path.join(os.getcwd(), "instance")
    os.makedirs(instance_path, exist_ok=True)
    app.instance_path = instance_path  # for clarity


# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask application with DB and docs."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Ensure instance dir for SQLite persistence
    _ensure_instance_dir(app)

    # Enable CORS broadly (adjust later for production)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    # API and docs
    api = Api(app)

    # Register blueprints
    from .routes.health import blp as health_blp
    api.register_blueprint(health_blp)

    # CLI: create-db for quick local setup
    @app.cli.command("create-db")
    def create_db():  # pragma: no cover
        """Create database tables using SQLAlchemy models (dev only)."""
        with app.app_context():
            db.create_all()
            print("Database tables created.")

    return app
