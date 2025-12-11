from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint("Health", "health", url_prefix="/", description="Health check endpoints")


@blp.route("/")
class HealthCheck(MethodView):
    """Root health-check endpoint returning a simple status JSON."""

    def get(self):
        """Returns a simple health status response."""
        return {"message": "Healthy"}
