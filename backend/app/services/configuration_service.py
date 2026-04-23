"""
Configuration Service - ConditionMap / Condition / Case / Run CRUD +
XML generation background task + Diff logic
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.configuration import Case, Condition, ConditionMap, ConditionMapFolder, CaseFolder, Run
from app.models.geometry import GeometryAssembly
from app.models.template import Template, TemplateVersion
from app.models.user import User
from app.schemas.configuration import CaseResponse, RunResponse

logger = logging.getLogger(__name__)
from app.schemas.configuration import (
    CaseCreate, CaseUpdate, CaseDuplicateRequest,
    CaseFolderCreate, CaseFolderUpdate,
    CaseCompareResult, PartsDiffResult,
    ConditionCreate, ConditionUpdate,
    ConditionMapCreate, ConditionMapUpdate,
    ConditionMapFolderCreate, ConditionMapFolderUpdate,
    DiffField, DiffResult,
    RunCreate, RunUpdate,
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
    if "folder_id" in data.model_fields_set:
        m.folder_id = data.folder_id
    db.commit()
    db.refresh(m)
    return m


def delete_map(db: Session, map_id: str, current_user: User) -> None:
    m = _get_map_or_404(db, map_id)
    _check_owner_or_admin(m, current_user)
    linked_cases = db.query(Case).filter(Case.map_id == map_id).count()
    if linked_cases > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete condition map: {linked_cases} case(s) are linked to it. "
                   "Unlink or delete those cases first.",
        )
    db.delete(m)
    db.commit()


# ---------------------------------------------------------------------------
# ConditionMap Folder CRUD
# ---------------------------------------------------------------------------

def _get_map_folder_or_404(db: Session, folder_id: str) -> ConditionMapFolder:
    f = db.get(ConditionMapFolder, folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="ConditionMap folder not found")
    return f


def list_map_folders(db: Session) -> list[ConditionMapFolder]:
    return list(db.scalars(select(ConditionMapFolder).order_by(ConditionMapFolder.name)).all())


def create_map_folder(db: Session, data: ConditionMapFolderCreate, current_user: User) -> ConditionMapFolder:
    f = ConditionMapFolder(name=data.name, description=data.description, created_by=current_user.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def update_map_folder(db: Session, folder_id: str, data: ConditionMapFolderUpdate, current_user: User) -> ConditionMapFolder:
    f = _get_map_folder_or_404(db, folder_id)
    if data.name is not None:
        f.name = data.name
    if data.description is not None:
        f.description = data.description
    db.commit()
    db.refresh(f)
    return f


def delete_map_folder(db: Session, folder_id: str, current_user: User) -> None:
    from sqlalchemy import update as sa_update
    f = _get_map_folder_or_404(db, folder_id)
    db.execute(sa_update(ConditionMap).where(ConditionMap.folder_id == folder_id).values(folder_id=None))
    db.delete(f)
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
    import json as _json
    _get_map_or_404(db, map_id)
    c = Condition(
        map_id=map_id,
        name=data.name,
        inflow_velocity=data.inflow_velocity,
        yaw_angle=data.yaw_angle,
        ride_height_json=_json.dumps(data.ride_height.model_dump()),
        yaw_config_json=_json.dumps(data.yaw_config.model_dump()),
        created_by=current_user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def update_condition(
    db: Session, map_id: str, condition_id: str, data: ConditionUpdate, current_user: User
) -> Condition:
    import json as _json
    c = _get_condition_or_404(db, map_id, condition_id)
    _check_owner_or_admin(c, current_user)
    if data.name is not None:
        c.name = data.name
    if data.inflow_velocity is not None:
        c.inflow_velocity = data.inflow_velocity
    if data.yaw_angle is not None:
        c.yaw_angle = data.yaw_angle
    if data.ride_height is not None:
        c.ride_height_json = _json.dumps(data.ride_height.model_dump())
    if data.yaw_config is not None:
        c.yaw_config_json = _json.dumps(data.yaw_config.model_dump())
    db.commit()
    db.refresh(c)
    return c


def delete_condition(db: Session, map_id: str, condition_id: str, current_user: User) -> None:
    c = _get_condition_or_404(db, map_id, condition_id)
    _check_owner_or_admin(c, current_user)
    linked_runs = db.query(Run).filter(Run.condition_id == condition_id).count()
    if linked_runs > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete condition: {linked_runs} run(s) are linked to it. "
                   "Delete those runs first.",
        )
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
    # Auto-generate case_number: count existing cases + 1
    n = db.scalar(select(func.count()).select_from(Case)) or 0
    case_number = f"C{n + 1:03d}"
    case = Case(
        case_number=case_number,
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
    if "template_id" in data.model_fields_set and data.template_id is not None:
        if not db.get(Template, data.template_id):
            raise HTTPException(status_code=404, detail="Template not found")
        case.template_id = data.template_id
    if "assembly_id" in data.model_fields_set and data.assembly_id is not None:
        if not db.get(GeometryAssembly, data.assembly_id):
            raise HTTPException(status_code=404, detail="Assembly not found")
        case.assembly_id = data.assembly_id
    if "map_id" in data.model_fields_set:
        if data.map_id and not db.get(ConditionMap, data.map_id):
            raise HTTPException(status_code=404, detail="ConditionMap not found")
        case.map_id = data.map_id
    if "folder_id" in data.model_fields_set:
        case.folder_id = data.folder_id
    if "parent_case_id" in data.model_fields_set:
        if data.parent_case_id and not db.get(Case, data.parent_case_id):
            raise HTTPException(status_code=404, detail="Parent case not found")
        case.parent_case_id = data.parent_case_id
    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: str, current_user: User) -> None:
    case = _get_case_or_404(db, case_id)
    _check_owner_or_admin(case, current_user)

    # Collect run IDs before cascade delete
    run_ids = [run.id for run in case.runs]

    db.delete(case)
    db.commit()

    # Delete run output directories from filesystem
    from app.services.geometry_service import _rmtree_force  # avoid circular import at module level
    for run_id in run_ids:
        run_dir = settings.runs_dir / run_id
        try:
            if run_dir.exists() and run_dir != settings.runs_dir:
                _rmtree_force(run_dir)
                logger.info("Deleted run directory: %s", run_dir)
        except Exception as e:
            logger.warning("Failed to delete run directory %s: %s", run_dir, e)


# ---------------------------------------------------------------------------
# Case Folder CRUD
# ---------------------------------------------------------------------------

def _get_case_folder_or_404(db: Session, folder_id: str) -> CaseFolder:
    f = db.get(CaseFolder, folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="Case folder not found")
    return f


def list_case_folders(db: Session) -> list[CaseFolder]:
    return list(db.scalars(select(CaseFolder).order_by(CaseFolder.name)).all())


def create_case_folder(db: Session, data: CaseFolderCreate, current_user: User) -> CaseFolder:
    f = CaseFolder(name=data.name, description=data.description, created_by=current_user.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def update_case_folder(db: Session, folder_id: str, data: CaseFolderUpdate, current_user: User) -> CaseFolder:
    f = _get_case_folder_or_404(db, folder_id)
    if data.name is not None:
        f.name = data.name
    if data.description is not None:
        f.description = data.description
    db.commit()
    db.refresh(f)
    return f


def delete_case_folder(db: Session, folder_id: str, current_user: User) -> None:
    from sqlalchemy import update as sa_update
    f = _get_case_folder_or_404(db, folder_id)
    db.execute(sa_update(Case).where(Case.folder_id == folder_id).values(folder_id=None))
    db.delete(f)
    db.commit()


def duplicate_case(db: Session, case_id: str, data: CaseDuplicateRequest, current_user: User) -> Case:
    """Create a new Case with the same template/assembly/map as an existing Case.
    Sets parent_case_id to the source case. Runs are NOT copied — the duplicate starts empty."""
    src = _get_case_or_404(db, case_id)
    n = db.scalar(select(func.count()).select_from(Case)) or 0
    case_number = f"C{n + 1:03d}"
    new_case = Case(
        case_number=case_number,
        name=data.name,
        description=data.description,
        template_id=src.template_id,
        assembly_id=src.assembly_id,
        map_id=src.map_id,
        parent_case_id=case_id,
        created_by=current_user.id,
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


def create_case_with_runs(db: Session, data: CaseCreate, current_user: User) -> Case:
    """Create Case and, if a ConditionMap is set, auto-generate one Run per Condition."""
    case = create_case(db, data, current_user)
    if case.map_id:
        conditions = list(
            db.scalars(
                select(Condition)
                .where(Condition.map_id == case.map_id)
                .order_by(Condition.created_at.asc())
            ).all()
        )
        for idx, cond in enumerate(conditions, start=1):
            run_number = f"{case.case_number}_R{idx:02d}"
            auto_name = f"{case.case_number}_R{idx:02d}_{cond.name}"
            run = Run(
                run_number=run_number,
                name=auto_name,
                case_id=case.id,
                condition_id=cond.id,
                status="pending",
                created_by=current_user.id,
            )
            db.add(run)
        db.commit()
    return case


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
    # Auto-generate run_number within this case
    run_count = db.scalar(select(func.count()).select_from(Run).where(Run.case_id == case_id)) or 0
    run_idx = run_count + 1
    run_number = f"{case.case_number}_R{run_idx:02d}"
    # Auto-format run name: {case_number}_{run_number_suffix}_{condition_name}[_{comment}]
    auto_name = f"{case.case_number}_R{run_idx:02d}_{condition.name}"
    if data.comment:
        auto_name = f"{auto_name}_{data.comment}"
    run = Run(
        run_number=run_number,
        name=data.name if data.name else auto_name,
        case_id=case_id,
        condition_id=data.condition_id,
        status="pending",
        created_by=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def delete_run(db: Session, case_id: str, run_id: str, current_user: User) -> None:
    """Delete a single Run and its output directory."""
    run = _get_run_or_404(db, case_id, run_id)
    _check_owner_or_admin(run, current_user)
    db.delete(run)
    db.commit()
    from app.services.geometry_service import _rmtree_force  # avoid circular import at module level
    run_dir = settings.runs_dir / run_id
    try:
        if run_dir.exists() and run_dir != settings.runs_dir:
            _rmtree_force(run_dir)
            logger.info("Deleted run directory: %s", run_dir)
    except Exception as e:
        logger.warning("Failed to delete run directory %s: %s", run_dir, e)


def reset_run(db: Session, case_id: str, run_id: str, current_user: User) -> Run:
    """Reset a Run back to pending state (clears xml/stl/error) and deletes its output dir."""
    run = _get_run_or_404(db, case_id, run_id)
    _check_owner_or_admin(run, current_user)
    from app.services.geometry_service import _rmtree_force
    run_dir = settings.runs_dir / run_id
    try:
        if run_dir.exists() and run_dir != settings.runs_dir:
            _rmtree_force(run_dir)
    except Exception as e:
        logger.warning("Failed to delete run directory %s: %s", run_dir, e)
    run.xml_path = None
    run.stl_path = None
    run.status = "pending"
    run.error_message = None
    db.commit()
    db.refresh(run)
    return run


def trigger_xml_generation(
    db: Session,
    case_id: str,
    run_id: str,
    current_user: User,
    background_tasks: BackgroundTasks,
    geometry_only: bool = False,
) -> Run:
    run = _get_run_or_404(db, case_id, run_id)
    _check_owner_or_admin(run, current_user)
    if run.status == "generating":
        raise HTTPException(status_code=409, detail="XML generation already in progress")
    run.status = "generating"
    db.commit()
    background_tasks.add_task(_generate_xml_task, run_id, geometry_only)
    return run


def update_run(
    db: Session,
    case_id: str,
    run_id: str,
    data: RunUpdate,
    current_user: User,
) -> Run:
    """Partial update of a Run (e.g. set geometry_override_id)."""
    run = _get_run_or_404(db, case_id, run_id)
    _check_owner_or_admin(run, current_user)
    if "geometry_override_id" in data.model_fields_set:
        run.geometry_override_id = data.geometry_override_id
    db.commit()
    db.refresh(run)
    return run


def _generate_xml_task(run_id: str, geometry_only: bool = False) -> None:
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

        # geometry_override_id: if set, use a single override geometry for this run
        # (e.g. a ride-height-transformed version) instead of the assembly's geometries
        override_geom = None
        if run.geometry_override_id:
            from app.models.geometry import Geometry as GeometryModel
            override_geom = db.get(GeometryModel, run.geometry_override_id)
            if override_geom and override_geom.analysis_result:
                import json as _json
                override_analysis = _json.loads(override_geom.analysis_result) if isinstance(override_geom.analysis_result, str) else override_geom.analysis_result
                merged_analysis = override_analysis

        source_file: str | None = None
        source_files: list[str] = []
        if override_geom:
            source_file = override_geom.original_filename
        elif assembly and assembly.geometries:
            geom_names = [g.original_filename for g in assembly.geometries]
            if len(geom_names) == 1:
                source_file = geom_names[0]
            else:
                source_files = geom_names

        from app.services.compute_engine import assemble_ufx_solver_deck, build_probe_csv_files, extract_pca_axes
        from app.ultrafluid.serializer import serialize_ufx

        template = db.get(Template, case.template_id)
        sim_type = template.sim_type if template else "aero"

        # Resolve STL file paths for PCA axis extraction
        stl_paths: list[Path] = []
        if override_geom:
            if override_geom.is_linked:
                stl_paths.append(Path(override_geom.file_path))
            else:
                stl_paths.append(settings.upload_dir / override_geom.file_path)
        elif assembly and assembly.geometries:
            for geom in assembly.geometries:
                if geom.is_linked:
                    stl_paths.append(Path(geom.file_path))
                else:
                    stl_paths.append(settings.upload_dir / geom.file_path)

        # geometry_only: parse parent Run's XML and swap source_file only — no re-assembly
        if geometry_only and case.parent_case_id:
            parent_ready = db.scalar(
                select(Run).where(
                    Run.case_id == case.parent_case_id,
                    Run.status == "ready",
                    Run.condition_id == run.condition_id,
                ).limit(1)
            ) or db.scalar(
                select(Run).where(
                    Run.case_id == case.parent_case_id,
                    Run.status == "ready",
                ).limit(1)
            )
            if parent_ready and parent_ready.xml_path and Path(parent_ready.xml_path).exists():
                from app.ultrafluid.parser import parse_ufx
                deck = parse_ufx(Path(parent_ready.xml_path).read_bytes())
                if source_file:
                    deck.geometry.source_file = source_file
                geom_only_bytes = serialize_ufx(deck)
                out_dir = settings.runs_dir / run_id
                out_dir.mkdir(parents=True, exist_ok=True)
                xml_path = out_dir / "output.xml"
                xml_path.write_bytes(geom_only_bytes)
                if stl_paths:
                    stl_dst = out_dir / "input.stl"
                    shutil.copy2(str(stl_paths[0]), str(stl_dst))
                    run.stl_path = str(stl_dst)
                run.xml_path = str(xml_path)
                run.status = "ready"
                run.error_message = None
                return  # skip full generation
            else:
                logger.warning(
                    "geometry_only=True but no ready parent run found for run %s; falling back to full generation",
                    run_id,
                )

        porous_patterns = [pc.part_name for pc in template_settings.porous_coefficients]
        rim_patterns = list(template_settings.target_names.rim)
        pca_axes = extract_pca_axes(stl_paths, porous_patterns, rim_patterns)

        deck = assemble_ufx_solver_deck(
            template_settings=template_settings,
            analysis_result=merged_analysis,
            sim_type=sim_type,
            inflow_velocity=condition.inflow_velocity,
            yaw_angle=condition.yaw_angle,
            source_file=source_file,
            source_files=source_files if source_files else None,
            pca_axes=pca_axes,
        )
        xml_bytes = serialize_ufx(deck)

        out_dir = settings.runs_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        xml_path = out_dir / "output.xml"
        xml_path.write_bytes(xml_bytes)

        # Save probe location CSV files alongside the XML (one per probe_file_instance)
        probe_csvs = build_probe_csv_files(template_settings)
        for csv_filename, csv_bytes in probe_csvs.items():
            (out_dir / csv_filename).write_bytes(csv_bytes)

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
        # Copy first STL into the run directory for later download
        if stl_paths:
            stl_dst = out_dir / "input.stl"
            shutil.copy2(str(stl_paths[0]), str(stl_dst))
            run.stl_path = str(stl_dst)
        run.status = "ready"
        run.error_message = None

    except Exception as exc:
        import traceback
        if run:
            run.status = "error"
            run.error_message = traceback.format_exc()
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


def get_axes_glb(db: Session, case_id: str, run_id: str) -> bytes:
    """Build and return a GLB visualising wheel-rotation axes and porous-flow axes
    for the assembly + template associated with the given Run."""
    run = _get_run_or_404(db, case_id, run_id)
    if run.status != "ready":
        raise HTTPException(status_code=400, detail="Run is not ready")

    case      = db.get(Case, run.case_id)
    condition = db.get(Condition, run.condition_id)

    active_version = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.template_id == case.template_id,
            TemplateVersion.is_active == True,  # noqa: E712
        )
    )
    if not active_version:
        raise HTTPException(status_code=404, detail="No active template version found")

    assembly = db.scalar(
        select(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .where(GeometryAssembly.id == case.assembly_id)
    )
    merged_analysis  = _merge_analysis_results(assembly)
    template_settings = TemplateSettings.model_validate(json.loads(active_version.settings))

    stl_paths: list[Path] = []
    if assembly and assembly.geometries:
        for geom in assembly.geometries:
            if geom.is_linked:
                stl_paths.append(Path(geom.file_path))
            else:
                stl_paths.append(settings.upload_dir / geom.file_path)

    from app.services.viewer_service import build_axes_glb
    try:
        return build_axes_glb(
            template_settings=template_settings,
            analysis_result=merged_analysis,
            stl_paths=stl_paths,
            inflow_velocity=condition.inflow_velocity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


# ---------------------------------------------------------------------------
# Response enrichment helpers
# ---------------------------------------------------------------------------

def compare_cases(db: Session, base_case_id: str, compare_case_id: str) -> CaseCompareResult:
    """Compare two Cases: template settings diff, map conditions diff, assembly parts diff."""
    base = _get_case_or_404(db, base_case_id)
    comp = _get_case_or_404(db, compare_case_id)

    # Template settings deep-diff
    base_tv = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.template_id == base.template_id,
            TemplateVersion.is_active == True,  # noqa: E712
        )
    )
    comp_tv = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.template_id == comp.template_id,
            TemplateVersion.is_active == True,  # noqa: E712
        )
    )
    base_settings = json.loads(base_tv.settings) if base_tv else {}
    comp_settings = json.loads(comp_tv.settings) if comp_tv else {}
    template_diff = _diff_dicts("", base_settings, comp_settings)

    # Map / conditions diff: flat representation {"condname.velocity": val, ...}
    def _conditions_flat(map_id: str | None) -> dict:
        if not map_id:
            return {}
        conds = list(
            db.scalars(
                select(Condition).where(Condition.map_id == map_id).order_by(Condition.name)
            ).all()
        )
        result: dict = {}
        for c in conds:
            result[f"{c.name}.inflow_velocity"] = c.inflow_velocity
            result[f"{c.name}.yaw_angle"] = c.yaw_angle
        return result

    map_diff = _diff_dicts("", _conditions_flat(base.map_id), _conditions_flat(comp.map_id))

    # Assembly parts diff
    base_assembly = db.scalar(
        select(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .where(GeometryAssembly.id == base.assembly_id)
    )
    comp_assembly = db.scalar(
        select(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .where(GeometryAssembly.id == comp.assembly_id)
    )
    base_analysis = _merge_analysis_results(base_assembly)
    comp_analysis = _merge_analysis_results(comp_assembly)
    base_parts = set(base_analysis.get("parts", []))
    comp_parts = set(comp_analysis.get("parts", []))
    parts_diff = PartsDiffResult(
        added=sorted(comp_parts - base_parts),
        removed=sorted(base_parts - comp_parts),
        common=sorted(base_parts & comp_parts),
    )

    return CaseCompareResult(
        base_case_id=base_case_id,
        compare_case_id=compare_case_id,
        base_case_number=base.case_number,
        compare_case_number=comp.case_number,
        template_settings_diff=template_diff,
        map_diff=map_diff,
        parts_diff=parts_diff,
    )


def enrich_case_response(db: Session, case: Case, run_count: int | None = None) -> CaseResponse:
    """Build CaseResponse with display name fields populated from related rows."""
    out = CaseResponse.model_validate(case)
    template = db.get(Template, case.template_id)
    assembly = db.get(GeometryAssembly, case.assembly_id)
    cmap = db.get(ConditionMap, case.map_id) if case.map_id else None
    out.template_name = template.name if template else ""
    out.assembly_name = assembly.name if assembly else ""
    out.map_name = cmap.name if cmap else ""
    if case.parent_case_id:
        parent = db.get(Case, case.parent_case_id)
        if parent:
            out.parent_case_number = parent.case_number
            out.parent_case_name = parent.name
    if run_count is None:
        rc = db.scalar(select(func.count()).select_from(Run).where(Run.case_id == case.id)) or 0
        out.run_count = rc
    else:
        out.run_count = run_count
    return out


def enrich_run_response(db: Session, run: Run) -> RunResponse:
    """Build RunResponse with condition display fields."""
    out = RunResponse.model_validate(run)
    condition = db.get(Condition, run.condition_id)
    if condition:
        out.condition_name = condition.name
        out.condition_velocity = condition.inflow_velocity
        out.condition_yaw = condition.yaw_angle
    return out
