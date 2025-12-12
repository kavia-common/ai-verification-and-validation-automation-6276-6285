from .app_factory import create_app

# Expose an app instance for simple runners while allowing factory usage
app = create_app()

__all__ = ["create_app", "app"]
