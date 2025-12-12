import os
from datetime import timedelta


class BaseConfig:
    """Base Flask configuration for the backend service with API docs enabled and DB via SQLAlchemy."""
    # Flask basics
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

    # API docs (flask-smorest)
    API_TITLE = "AI V&V Test Automation API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = ""
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Database
    # Default to SQLite file in instance folder if DATABASE_URL not provided
    DEFAULT_SQLITE_PATH = os.path.join(os.getcwd(), "instance", "app.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_SQLITE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security and sessions
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False


def get_config() -> type:
    """Resolve config class based on REACT_APP_NODE_ENV or FLASK_ENV."""
    env = os.getenv("REACT_APP_NODE_ENV") or os.getenv("FLASK_ENV") or "development"
    env = env.lower()
    if env.startswith("prod"):
        return ProductionConfig
    if env.startswith("test"):
        return TestingConfig
    return DevelopmentConfig
