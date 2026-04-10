"""
test_xml_generation.py — XML 生成エンドツーエンドテスト

DB から Template (active version) と Geometry (ready) を取得し、
assemble_ufx_solver_deck → serialize_ufx → XML ファイル書き出しまでを検証する。

Usage:
    uv run python scripts/test_xml_generation.py
    uv run python scripts/test_xml_generation.py --template-id <id> --geometry-id <id>
    uv run python scripts/test_xml_generation.py --list   # DB 内のデータ一覧を表示
"""
import argparse
import json
import sys
from pathlib import Path

# backend/ を sys.path に追加して app を import できるようにする
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models.user import User  # noqa: F401 — required for SQLAlchemy relationship resolution
from app.models.template import Template, TemplateVersion
from app.models.geometry import Geometry
from app.models.configuration import Case, ConditionMap, Condition, Run  # noqa: F401
from app.schemas.template_settings import TemplateSettings
from app.services.compute_engine import assemble_ufx_solver_deck
from app.ultrafluid.serializer import serialize_ufx


def list_data(db) -> None:
    """DB 内のテンプレートとジオメトリを一覧表示する。"""
    templates = db.query(Template).all()
    print(f"\n{'='*60}")
    print(f"Templates: {len(templates)}")
    print(f"{'='*60}")
    for t in templates:
        active = next((v for v in t.versions if v.is_active), None)
        print(f"  ID: {t.id}")
        print(f"  Name: {t.name}  Type: {t.sim_type}")
        if active:
            print(f"  Active version: v{active.version_number} (id={active.id})")
        else:
            print(f"  Active version: (none)")
        print()

    geometries = db.query(Geometry).all()
    print(f"{'='*60}")
    print(f"Geometries: {len(geometries)}")
    print(f"{'='*60}")
    for g in geometries:
        has_result = bool(g.analysis_result)
        print(f"  ID: {g.id}")
        print(f"  Name: {g.name}  Status: {g.status}  has_result: {has_result}")
        print()


def get_template_version(db, template_id: str | None) -> TemplateVersion | None:
    """アクティブな TemplateVersion を取得する。"""
    if template_id:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            print(f"[ERROR] Template not found: {template_id}")
            return None
    else:
        template = db.query(Template).first()
        if not template:
            return None

    active = next((v for v in template.versions if v.is_active), None)
    if not active and template.versions:
        active = template.versions[-1]
    return active


def get_geometry(db, geometry_id: str | None) -> Geometry | None:
    """解析済みの Geometry を取得する。"""
    if geometry_id:
        geo = db.query(Geometry).filter(Geometry.id == geometry_id).first()
        if not geo:
            print(f"[ERROR] Geometry not found: {geometry_id}")
            return None
        return geo
    else:
        # status=ready を優先、なければ analysis_result があるものを返す
        geo = db.query(Geometry).filter(Geometry.status == "ready").first()
        if not geo:
            geo = db.query(Geometry).filter(Geometry.analysis_result.isnot(None)).first()
        return geo


def main() -> None:
    parser = argparse.ArgumentParser(description="XML generation test")
    parser.add_argument("--template-id", default=None, help="Template ID (auto-detect if omitted)")
    parser.add_argument("--geometry-id", default=None, help="Geometry ID (auto-detect if omitted)")
    parser.add_argument("--list", action="store_true", help="List available templates and geometries")
    parser.add_argument("--output", default="test_xml_output.xml", help="Output XML file path")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.list:
            list_data(db)
            return

        # ── Template version ──────────────────────────────────────────────
        version = get_template_version(db, args.template_id)
        if version is None:
            print("[ERROR] No template found in DB.")
            print()
            print("Register a template first:")
            print("  1. Start the backend: uv run uvicorn app.main:app --reload")
            print("  2. Open http://localhost:8000/docs")
            print("  3. POST /api/v1/templates/ to create a template")
            print("  (or run with --list to check current DB state)")
            sys.exit(1)

        print(f"[OK] Template: {version.template.name}  v{version.version_number}")

        # ── TemplateSettings を parse ──────────────────────────────────────
        raw_settings = version.settings
        if isinstance(raw_settings, str):
            raw_settings = json.loads(raw_settings)
        template_settings = TemplateSettings.model_validate(raw_settings)
        print("[OK] TemplateSettings parsed")

        # ── Geometry ───────────────────────────────────────────────────────
        geo = get_geometry(db, args.geometry_id)
        if geo is None:
            print("[ERROR] No geometry with analysis_result found in DB.")
            print()
            print("Upload and analyze a geometry first:")
            print("  1. Start the backend: uv run uvicorn app.main:app --reload")
            print("  2. POST /api/v1/geometries/ (multipart STL upload)")
            print("  3. Wait for status='ready'")
            sys.exit(1)

        if not geo.analysis_result:
            print(f"[ERROR] Geometry '{geo.name}' has no analysis_result (status={geo.status})")
            sys.exit(1)

        print(f"[OK] Geometry: {geo.name}  status={geo.status}")

        # ── analysis_result を parse ───────────────────────────────────────
        raw_result = geo.analysis_result
        if isinstance(raw_result, str):
            analysis_result = json.loads(raw_result)
        else:
            analysis_result = raw_result

        parts = analysis_result.get("parts", [])
        print(f"[OK] analysis_result: {len(parts)} parts")

        # ── 実行パラメータ ─────────────────────────────────────────────────
        inflow_velocity = template_settings.simulation_parameter.inflow_velocity
        yaw_angle = template_settings.simulation_parameter.yaw_angle
        source_file = geo.original_filename or geo.name

        print(f"[INFO] inflow_velocity={inflow_velocity} m/s  yaw={yaw_angle} deg")
        print(f"[INFO] source_file={source_file}")

        # ── assemble ───────────────────────────────────────────────────────
        print("\n[STEP] Assembling UfxSolverDeck...")
        deck = assemble_ufx_solver_deck(
            template_settings=template_settings,
            analysis_result=analysis_result,
            inflow_velocity=inflow_velocity,
            yaw_angle=yaw_angle,
            source_file=source_file,
        )
        print("[OK] UfxSolverDeck assembled")

        # ── serialize ──────────────────────────────────────────────────────
        print("[STEP] Serializing to XML...")
        xml_bytes = serialize_ufx(deck)
        print(f"[OK] Serialized: {len(xml_bytes):,} bytes")

        # ── write ──────────────────────────────────────────────────────────
        out_path = Path(args.output)
        out_path.write_bytes(xml_bytes)
        print(f"\n[SUCCESS] XML written to: {out_path.resolve()}")

        # ── サマリー ───────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"  Template   : {version.template.name} v{version.version_number}")
        print(f"  Geometry   : {geo.name}")
        print(f"  Parts      : {len(parts)}")
        vbbox = analysis_result.get("vehicle_bbox", {})
        if vbbox:
            dims = analysis_result.get("vehicle_dimensions", {})
            length = dims.get("length", 0)
            width = dims.get("width", 0)
            height = dims.get("height", 0)
            print(f"  Vehicle L/W/H: {length:.3f} / {width:.3f} / {height:.3f} m")
        print(f"  XML size   : {len(xml_bytes):,} bytes")
        print(f"  Output     : {out_path.resolve()}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
