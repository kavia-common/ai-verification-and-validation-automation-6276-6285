import os
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

# Import blueprints
from .routes.health import blp as health_blp
from .routes.srs import blp as srs_blp
from .routes.generation import blp as generation_blp
from .routes.execution import blp as execution_blp
from .routes.reports import blp as reports_blp

# Directories for filesystem storage
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(BASE_DIR, "input")
CODEBASE_DIR = os.path.join(BASE_DIR, "codebase")
RUNS_DIR = os.path.join(BASE_DIR, "runs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def ensure_directories():
    """Ensure required directories exist at startup."""
    for path in [INPUT_DIR, CODEBASE_DIR, RUNS_DIR, REPORTS_DIR]:
        os.makedirs(path, exist_ok=True)


# Initialize Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# Enable CORS for all origins (adjust as needed)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# OpenAPI/Swagger configuration
app.config["API_TITLE"] = "AI Test Automation API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Initialize API
api = Api(app)

# Ensure directories
ensure_directories()

# Register blueprints
api.register_blueprint(health_blp)
api.register_blueprint(srs_blp)
api.register_blueprint(generation_blp)
api.register_blueprint(execution_blp)
api.register_blueprint(reports_blp)
