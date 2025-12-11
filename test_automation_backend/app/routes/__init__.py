# Routes package initializer
# Expose blueprints for registration at app startup

from .health import blp as health_blp  # noqa: F401
from .srs import blp as srs_blp  # noqa: F401
from .generation import blp as generation_blp  # noqa: F401
from .execution import blp as execution_blp  # noqa: F401
from .reports import blp as reports_blp  # noqa: F401
