import json
import os
from app import app, api  # import Flask app and Api instance

with app.app_context():
    # Ensure all blueprints are registered and spec is up to date
    openapi_spec = api.spec.to_dict()

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
    print(f"OpenAPI spec written to {output_path}")
