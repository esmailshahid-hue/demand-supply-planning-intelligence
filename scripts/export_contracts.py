"""Generate the source OpenAPI schema consumed by openapi-typescript."""
import json
from pathlib import Path
from backend.app.main import app

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
