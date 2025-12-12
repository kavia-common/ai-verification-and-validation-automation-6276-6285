from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# SQLAlchemy DB instance (initialized in app factory)
db = SQLAlchemy()
# Marshmallow instance for serialization (if needed later)
ma = Marshmallow()
