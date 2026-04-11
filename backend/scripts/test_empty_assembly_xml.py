"""Test XML generation with an empty assembly (no geometries) — reproduces KeyError 'x_min'."""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to resolve SQLAlchemy relationships
import app.models.user  # noqa: F401
import app.models.template  # noqa: F401
import app.models.geometry  # noqa: F401
import app.models.configuration  # noqa: F401
from app.database import SessionLocal
from app.models.configuration import Case
from app.models.template import Template, TemplateVersion
from app.schemas.template_settings import TemplateSettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

db = SessionLocal()

case_id = "985f7041-8d01-4ca4-bbd0-ab3499300617"
case = db.get(Case, case_id)
print(f"Case: {case.name if case else 'NOT FOUND'}")

template = db.get(Template, case.template_id)
print(f"Template: {template.name}, sim_type={template.sim_type}")

active_version = db.scalar(
    select(TemplateVersion).where(
        TemplateVersion.template_id == case.template_id,
        TemplateVersion.is_active == True,
    )
)
template_settings = TemplateSettings.model_validate(json.loads(active_version.settings))

# Empty analysis result — same as empty assembly
merged_analysis = {"parts": [], "vehicle_bbox": {}, "vehicle_dimensions": {}, "part_info": {}}

from app.services.compute_engine import assemble_ufx_solver_deck

try:
    deck = assemble_ufx_solver_deck(
        template_settings=template_settings,
        analysis_result=merged_analysis,
        sim_type=template.sim_type,
        inflow_velocity=38.88,
        yaw_angle=0.0,
        source_file="test.stl",
    )
    print("SUCCESS — deck assembled")
except Exception:
    print("ERROR:")
    traceback.print_exc()
finally:
    db.close()
