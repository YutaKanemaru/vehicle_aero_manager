"""
Dump TemplateSettings Pydantic defaults to JSON.
Called as part of `npm run generate-api` in the frontend.

Output: backend/template_defaults.json
"""
import json
import sys
from pathlib import Path

# Ensure backend/app is importable when run from backend/ directory
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.template_settings import TemplateSettings

output_path = Path(__file__).parent / "template_defaults.json"
defaults = TemplateSettings().model_dump(mode="json")
json.dump(defaults, output_path.open("w"), indent=2)
print(f"Generated {output_path}")
