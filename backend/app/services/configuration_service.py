"""
Configuration Service - ConditionMap / Condition / Case / Run CRUD +
XML generation background task + Diff logic
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.configuration import Case, Condition, ConditionMap, Run
from app.models.geometry import GeometryAssembly
from app.models.template import Template, TemplateVersion
from app.models.user import User
from app.schemas.configuration import (
    CaseCreate, CaseUpdate,
    ConditionCreate, ConditionUpdate,
    ConditionMapCreate, ConditionMapUpdate,
    DiffField, DiffResult,
    RunCreate,
)
from app.schemas.template_settings import TemplateSettings


def _check_owner_or_admin(resource, current_user: User) -> None:
    if resource.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")


def _get_map_or_404(db: Session, map_id: str) -> ConditionMap:
    m = db.get(ConditionMap, map_id)
    if not m:
        raise HTTPException(status_code=404, detail="ConditionMap not found")
    return m


def _get_condition_or_404(db: Session, map_id: str, condition_id: str) -> Condition:
    c = db.scalar(
        select(Condition).where(
            Condition.id == condition_id,
            Condition.map_id == map_id,
        )
    )
    if not c:
        raise HTTPException(status_code=404, detail="Condition not found")
    return c


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _get_run_or_404(db: Session, case_id: str, run_id: str) -> Run:
    run = db.scalar(
        select(Run).where(
            Run.id == run_id,
            Run.case_id == case_id,
        )
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# ---------------------------------------------------------------------------
# ConditionMap CRUD
# ---------------------------------------------------------------------------

def list_maps(db: Session) -> list[ConditionMap]:
    return list(
        db.scalars(
            select(ConditionMap)
            .options(selectinload(ConditionMap.conditions))
            .order_by(ConditionMap.created_at.desc())
        ).all()
    )


def get_map(db: Session, map_id: str) -> ConditionMap:
    m = db.scalar(
        select(ConditionMap)
        .options(selectinload(ConditionMap.conditions))
        .where(ConditionMap.id == map_id)
    )
    if not m:
        raise HTTPException(status_code=404, detail="ConditionMap not found")
    return m


def create_map(db: Session, data: ConditionMapCreate, current_user: User) -> ConditionMap:
    m = ConditionMap(
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def update_map(db: Session, map_id: str, data: ConditionMapUpdate, current_user: User) -> ConditionMap:
    m = _get_map_or_404(db, map_id)
    _check_owner_or_admin(m, current_user)
    if data.name is not None:
        m.name = data.name
    if data.description is not None:
        m.description = data.description
    db.commit()
    db.refresh(m)
    return m


def delete_map(db: Session, map_id: str, current_user: User) -> None:
    m = _get_map_or_404(db, map_id)
    _check_owner_or_admin(m, current_user)
    db.delete(m)
    db.commit()


# ---------------------------------------------------------------------------
# Condition CRUD
# ---------------------------------------------------------------------------

def list_conditions(db: Session, map_id: str) -> list[Condition]:
    _get_map_or_404(db, map_id)
    return list(
        db.scalars(
            select(Condition)
            .where(Condition.map_id == map_id)
            .order_by(Condition.created_at.asc())
        ).all()
    )


def get_condition(db: Session, map_id: str, condition_id: str) -> Condition:
    return _get_condition_or_404(db, map_id, condition_id)


def create_condition(db: Session, map_id: str, data: ConditionCreate, current_user: User) -> Condition:
    _get_map_or_404(db, map_id)
    c = Condition(
        map_id=map_id,
        name=data.name,
        inflow_velocity=data.inflow_velocity,
        yaw_angle=data.yaw_angle,
        created_by=current_user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def update_condition(
    db: Session, map_id: str, condition_id: str, data: ConditionUpdate, current_user: User
) -> Condition:
    c = _get_condition_or_404(db, map_id, condition_id)
    _check_owner_or_admin(c, current_user)
    if data.name is not None:
        c.name = data.name
    if data.inflow_velocity is not None:
        c.inflow_velocity = data.inflow_velocity
    if data.yaw_angle is not None:
        c.yaw_angle = data.yaw_angle
    db.commit()
    db.refresh(c)
    return c


def delete_condition(db: Session, map_id: str, condition_id: str, current_user: User) -> None:
    c = _get_condition_or_404(db, map_id, condition_id)
    _check_owner_or_admin(c, current_user)
    db.delete(c)
    db.commit()


# ---------------------------------------------------------------------------
# Case CRUD
# ---------------------------------------------------------------------------

def list_cases(db: Session) -> list[Case]:
    return list(db.scalars(select(Case).order_by(Case.created_at.desc())).all())


def get_case(db: Session, case_id: str) -> Case:
    return _get_case_or_404(db, case_id)


def create_case(db: Session, data: CaseCreate, current_user: User) -> Case:
    if not db.get(Template, data.template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    if not db.get(GeometryAssembly, data.assembly_id):
        raise HTTPException(status_code=404, detail="Assembly not found")
    if data.map_id and not db.get(ConditionMap, data.map_id):
        raise HTTPException(status_code=404, detail="ConditionMap not found")
    case = Case(
        name=data.name,
        description=data.description,
        template_id=data.template_id,
        assembly_id=data.assembly_id,
        map_id=data.map_id,
        created_by=current_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_case(db: Session, case_id: str, data: CaseUpdate, current_user: User) -> Case:
    case = _get_case_or_404(db, case_id)
    _check_owner_or_admin(case, current_user)
    if data.name is not None:
        case.name = data.name
    if data.description is not None:
        case.description = data.description
    if "map_id" in data.model_fields_set:
        if data.map_id and not db.get(ConditionMap, data.map_id):
            raise HTTPException(status_code=404, detail="ConditionMap not found")
        case.map_id = data.map_id
    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: str, current_user: User) -> None:
    case = _get_case_or_404(db, case_id)
    _check_owner_or_admin(case, current_user)
    db.delete(case)
    db.commit()


# ---------------------------------------------------------------------------
# Run CRUD
# ---------------------------------------------------------------------------

def list_runs(db: Session, case_id: str) -> list[Run]:
    _get_case_or_404(db, case_id)
    return list(
        db.scalars(
            select(Run)
            .where(Run.case_id == case_id)
            .order_by(Run.created_at.desc())
        ).all()
    )


def create_run(db: Session, case_id: str, data: RunCreate, current_user: User) -> Run:
    case = _get_case_or_404(db, case_id)
    # Validate that condition belongs to this case's map
    condition = db.get(Condition, data.condition_id)
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    if case.map_id is None or condition.map_id != case.map_id:
        raise HTTPException(
            status_code=422,
            detail="Condition does not belong to the Case's ConditionMap",
        )
    run = Run(
        name=data.name,
        case_id=case_id,
        condition_id=data.condition_id,
        status="pending",
        created_by=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def trigger_xml_generation(
    db: Session,
    case_id: str,
    run_id: str,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> Run:
    run = _get_run_or_404(db, case_id, run_id)
    _check_owner_or_admin(run, current_user)
    if run.status == "generating":
        raise HTTPException(status_code=409, detail="XML generation already in progress")
    run.status = "generating"
    db.commit()
    background_tasks.add_task(_generate_xml_task, run_id)
    return run


def _generate_xml_task(run_id: str) -> None:
    from app.database import SessionLocal
    db = SessionLocal()
    run = None
    try:
        run = db.get(Run, run_id)
        if not run:
            return

        case = db.get(Case, run.case_id)
        condition = db.get(Condition, run.condition_id)

        active_version = db.scalar(
            select(TemplateVersion).where(
                TemplateVersion.template_id == case.template_id,
                TemplateVersion.is_active == True,  # noqa: E712
            )
        )
        if not active_version:
            run.status = "error"
            run.error_message = "No active template version found"
            db.commit()
            return

        assembly = db.scalar(
            select(GeometryAssembly)
            .options(selectinload(GeometryAssembly.geometries))
            .where(GeometryAssembly.id == case.assembly_id)
        )
        merged_analysis = _merge_analysis_results(assembly)
        template_settings = TemplateSettings.model_validate(json.loads(active_version.settings))

        source_file = "geometry.stl"
        if assembly and assembly.geometries:
            source_file = assembly.geometries[0].original_filename

        from app.services.compute_engine import assemble_ufx_solver_deck
        from app.ultrafluid.serializer import serialize_ufx

        deck = assemble_ufx_solver_deck(
            template_settings=template_settings,
            analysis_result=merged_analysis,
            inflow_velocity=condition.inflow_velocity,
            yaw_angle=condition.yaw_angle,
            source_file=source_file,
        )
        xml_bytes = serialize_ufx(deck)

        out_dir = settings.runs_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        xml_path = out_dir / "output.xml"
        xml_path.write_bytes(xml_bytes)

        # JSON snapshots — human-readable debug files, DB is the source of truth
        (out_dir / "template_settings.json").write_text(
            template_settings.model_dump_json(indent=2), encoding="utf-8"
        )
        (out_dir / "analysis_result.json").write_text(
            json.dumps(merged_analysis, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / "inputs.json").write_text(
            json.dumps(
                {
                    "inflow_velocity": condition.inflow_velocity,
                    "yaw_angle": condition.yaw_angle,
                    "source_file": source_file,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        run.xml_path = str(xml_path)
        run.status = "ready"
        run.error_message = None

    except Exception as exc:
        if run:
            run.status = "error"
            run.error_message = str(exc)
    finally:
        db.commit()
        db.close()


def _merge_analysis_results(assembly: GeometryAssembly | None) -> dict:
    if not assembly or not assembly.geometries:
        return {"parts": [], "vehicle_bbox": {}, "vehicle_dimensions": {}, "part_info": {}}
    merged_parts: list[str] = []
    merged_part_info: dict = {}
    all_bboxes: list[dict] = []
    for geom in assembly.geometries:
        if not geom.analysis_result:
            continue
        result = json.loads(geom.analysis_result)
        merged_parts.extend(result.get("parts", []))
        merged_part_info.update(result.get("part_info", {}))
        if result.get("vehicle_bbox"):
            all_bboxes.append(result["vehicle_bbox"])
    if not all_bboxes:
        vehicle_bbox: dict = {}
        vehicle_dimensions: dict = {}
    else:
        vehicle_bbox = {
            "x_min": min(b["x_min"] for b in all_bboxes),
            "x_max": max(b["x_max"] for b in all_bboxes),
            "y_min": min(b["y_min"] for b in all_bboxes),
            "y_max": max(b["y_max"] for b in all_bboxes),
            "z_min": min(b["z_min"] for b in all_bboxes),
            "z_max": max(b["z_max"] for b in all_bboxes),
        }
        vehicle_dimensions = {
            "length": vehicle_bbox["x_max"] - vehicle_bbox["x_min"],
            "width":  vehicle_bbox["y_max"] - vehicle_bbox["y_min"],
            "height": vehicle_bbox["z_max"] - vehicle_bbox["z_min"],
        }
    return {
        "parts": merged_parts,
        "vehicle_bbox": vehicle_bbox,
        "vehicle_dimensions": vehicle_dimensions,
        "part_info": merged_part_info,
    }


def get_xml_path(db: Session, case_id: str, run_id: str) -> Path:
    run = _get_run_or_404(db, case_id, run_id)
    if run.status != "ready" or not run.xml_path:
        raise HTTPException(status_code=404, detail="XML not ready")
    path = Path(run.xml_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="XML file not found on disk")
    return path


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def get_diff(db: Session, run_id_a: str, run_id_b: str) -> DiffResult:
    def _find_run(rid: str) -> Run:
        r = db.get(Run, rid)
        if not r:
            raise HTTPException(status_code=404, detail=f"Run {rid} not found")
        return r

    run_a = _find_run(run_id_a)
    run_b = _find_run(run_id_b)
    cond_a = db.get(Condition, run_a.condition_id)
    cond_b = db.get(Condition, run_b.condition_id)

    def _condition_dict(c: Condition | None) -> dict:
        if not c:
            return {}
        return {
            "name": c.name,
            "inflow_velocity": c.inflow_velocity,
            "yaw_angle": c.yaw_angle,
        }

    changed = _diff_dicts("", _condition_dict(cond_a), _condition_dict(cond_b))
    return DiffResult(run_a_id=run_id_a, run_b_id=run_id_b, changed_fields=changed)


def _diff_dicts(prefix: str, a: dict, b: dict) -> list[DiffField]:
    result: list[DiffField] = []
    keys = set(a) | set(b)
    for key in sorted(keys):
        full_key = f"{prefix}.{key}" if prefix else key
        va, vb = a.get(key), b.get(key)
        if isinstance(va, dict) and isinstance(vb, dict):
            result.extend(_diff_dicts(full_key, va, vb))
        elif va != vb:
            result.append(DiffField(
                field=full_key,
                run_a_value=str(va) if va is not None else None,
                run_b_value=str(vb) if vb is not None else None,
            ))
    return result
