from flask_smorest import Blueprint
from flask.views import MethodView

# Keep original label to match existing interfaces/openapi.json tag
blp = Blueprint("Healt Check", "health", url_prefix="/", description="Health check route")


@blp.route("/")
class HealthCheck(MethodView):
    """Health check endpoint to verify the server is running."""
    def get(self):
        return {"message": "Healthy"}
