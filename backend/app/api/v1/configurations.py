"""
API router: ConditionMap / Condition / Case / Run management
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.configuration import Case, ConditionMap, Run
from app.models.user import User
from app.schemas.configuration import (
    CaseCreate, CaseResponse, CaseUpdate, CaseDuplicateRequest,
    CaseFolderCreate, CaseFolderUpdate, CaseFolderResponse,
    CaseCompareResult,
    ConditionCreate, ConditionResponse, ConditionUpdate,
    ConditionMapCreate, ConditionMapResponse, ConditionMapUpdate,
    ConditionMapFolderCreate, ConditionMapFolderUpdate, ConditionMapFolderResponse,
    DiffResult,
    RunCreate, RunResponse, RunUpdate,
    SyncRunsPreview,
)
from app.services import configuration_service

router = APIRouter()


# ---------------------------------------------------------------------------
# ConditionMap endpoints  /maps/...
# ---------------------------------------------------------------------------

@router.get("/maps/", response_model=list[ConditionMapResponse])
def list_maps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    maps = configuration_service.list_maps(db)
    result = []
    for m in maps:
        data = ConditionMapResponse.model_validate(m)
        data.condition_count = len(m.conditions)
        result.append(data)
    return result


@router.post("/maps/", response_model=ConditionMapResponse, status_code=201)
def create_map(
    data: ConditionMapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = configuration_service.create_map(db, data, current_user)
    out = ConditionMapResponse.model_validate(m)
    out.condition_count = len(m.conditions)
    return out



# ---------------------------------------------------------------------------
# Map Folders — must be declared BEFORE /maps/{map_id}
# ---------------------------------------------------------------------------

@router.get("/maps/folders/", response_model=list[ConditionMapFolderResponse])
def list_map_folders(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return configuration_service.list_map_folders(db)


@router.post("/maps/folders/", response_model=ConditionMapFolderResponse, status_code=201)
def create_map_folder(
    data: ConditionMapFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.create_map_folder(db, data, current_user)


@router.patch("/maps/folders/{folder_id}", response_model=ConditionMapFolderResponse)
def update_map_folder(
    folder_id: str,
    data: ConditionMapFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.update_map_folder(db, folder_id, data, current_user)


@router.delete("/maps/folders/{folder_id}", status_code=204)
def delete_map_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_map_folder(db, folder_id, current_user)


@router.get("/maps/{map_id}", response_model=ConditionMapResponse)
def get_map(
    map_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = configuration_service.get_map(db, map_id)
    out = ConditionMapResponse.model_validate(m)
    out.condition_count = len(m.conditions)
    return out


@router.patch("/maps/{map_id}", response_model=ConditionMapResponse)
def update_map(
    map_id: str,
    data: ConditionMapUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = configuration_service.update_map(db, map_id, data, current_user)
    out = ConditionMapResponse.model_validate(m)
    out.condition_count = len(m.conditions)
    return out


@router.delete("/maps/{map_id}", status_code=204)
def delete_map(
    map_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_map(db, map_id, current_user)


# ---------------------------------------------------------------------------
# Condition endpoints  /maps/{map_id}/conditions/...
# ---------------------------------------------------------------------------

@router.get("/maps/{map_id}/conditions/", response_model=list[ConditionResponse])
def list_conditions(
    map_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.list_conditions(db, map_id)


@router.post("/maps/{map_id}/conditions/", response_model=ConditionResponse, status_code=201)
def create_condition(
    map_id: str,
    data: ConditionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.create_condition(db, map_id, data, current_user)


@router.get("/maps/{map_id}/conditions/{condition_id}", response_model=ConditionResponse)
def get_condition(
    map_id: str,
    condition_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.get_condition(db, map_id, condition_id)


@router.patch("/maps/{map_id}/conditions/{condition_id}", response_model=ConditionResponse)
def update_condition(
    map_id: str,
    condition_id: str,
    data: ConditionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.update_condition(db, map_id, condition_id, data, current_user)


@router.delete("/maps/{map_id}/conditions/{condition_id}", status_code=204)
def delete_condition(
    map_id: str,
    condition_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_condition(db, map_id, condition_id, current_user)


# ---------------------------------------------------------------------------
# Case endpoints  /cases/...
# ---------------------------------------------------------------------------

@router.get("/cases/", response_model=list[CaseResponse])
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cases = configuration_service.list_cases(db)
    return [configuration_service.enrich_case_response(db, c) for c in cases]


@router.post("/cases/", response_model=CaseResponse, status_code=201)
def create_case(
    data: CaseCreate,
    with_runs: bool = Query(False, description="Auto-create Runs for all Conditions in the map"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if with_runs:
        case = configuration_service.create_case_with_runs(db, data, current_user)
    else:
        case = configuration_service.create_case(db, data, current_user)
    return configuration_service.enrich_case_response(db, case)



# ---------------------------------------------------------------------------
# Case Folders -- must be declared BEFORE /cases/{case_id}
# ---------------------------------------------------------------------------

@router.get("/cases/folders/", response_model=list[CaseFolderResponse])
def list_case_folders(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return configuration_service.list_case_folders(db)


@router.post("/cases/folders/", response_model=CaseFolderResponse, status_code=201)
def create_case_folder(
    data: CaseFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.create_case_folder(db, data, current_user)


@router.patch("/cases/folders/{folder_id}", response_model=CaseFolderResponse)
def update_case_folder(
    folder_id: str,
    data: CaseFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.update_case_folder(db, folder_id, data, current_user)


@router.delete("/cases/folders/{folder_id}", status_code=204)
def delete_case_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_case_folder(db, folder_id, current_user)


@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = configuration_service.get_case(db, case_id)
    return configuration_service.enrich_case_response(db, c)


@router.get("/cases/{case_id}/sync-preview", response_model=SyncRunsPreview)
def sync_preview(
    case_id: str,
    new_map_id: str = Query(..., description="ID of the target ConditionMap"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what happens to Runs when this Case switches to a different map."""
    return configuration_service.compute_sync_preview(db, case_id, new_map_id)


@router.patch("/cases/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = configuration_service.update_case(db, case_id, data, current_user)
    return configuration_service.enrich_case_response(db, c)


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_case(db, case_id, current_user)


@router.post("/cases/{case_id}/duplicate", response_model=CaseResponse, status_code=201)
def duplicate_case(
    case_id: str,
    data: CaseDuplicateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = configuration_service.duplicate_case(db, case_id, data, current_user)
    return configuration_service.enrich_case_response(db, c)


# ---------------------------------------------------------------------------
# Run endpoints  /cases/{case_id}/runs/...
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/runs/", response_model=list[RunResponse])
def list_runs(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runs = configuration_service.list_runs(db, case_id)
    return [configuration_service.enrich_run_response(db, r) for r in runs]


@router.post("/cases/{case_id}/runs/", response_model=RunResponse, status_code=201)
def create_run(
    case_id: str,
    data: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = configuration_service.create_run(db, case_id, data, current_user)
    return configuration_service.enrich_run_response(db, run)


@router.patch("/cases/{case_id}/runs/{run_id}", response_model=RunResponse)
def update_run(
    case_id: str,
    run_id: str,
    data: RunUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = configuration_service.update_run(db, case_id, run_id, data, current_user)
    return configuration_service.enrich_run_response(db, run)


@router.post("/cases/{case_id}/runs/{run_id}/generate", response_model=RunResponse)
def generate_xml(
    case_id: str,
    run_id: str,
    background_tasks: BackgroundTasks,
    geometry_only: bool = Query(False, description="Swap STL only, reuse parent Run XML (requires parent_case_id)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = configuration_service.trigger_xml_generation(
        db, case_id, run_id, current_user, background_tasks, geometry_only
    )
    return configuration_service.enrich_run_response(db, run)


@router.delete("/cases/{case_id}/runs/{run_id}", status_code=204)
def delete_run(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    configuration_service.delete_run(db, case_id, run_id, current_user)


@router.post("/cases/{case_id}/runs/{run_id}/reset", response_model=RunResponse)
def reset_run(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = configuration_service.reset_run(db, case_id, run_id, current_user)
    return configuration_service.enrich_run_response(db, run)


@router.get("/cases/{case_id}/runs/{run_id}/download")
def download_xml(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = configuration_service.get_xml_path(db, case_id, run_id)
    return FileResponse(
        str(path),
        media_type="application/xml",
        filename=path.name,
    )


@router.get("/cases/{case_id}/runs/{run_id}/download-stl")
def download_stl(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the input STL that was used for XML generation."""
    from pathlib import Path as _Path
    from fastapi import HTTPException
    run = db.query(Run).filter_by(id=run_id, case_id=case_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.stl_path or not _Path(run.stl_path).exists():
        raise HTTPException(status_code=404, detail="STL file not available for this run")
    p = _Path(run.stl_path)
    return FileResponse(str(p), media_type="application/octet-stream", filename=p.name)


@router.get("/cases/{case_id}/runs/{run_id}/axes-glb")
def get_axes_glb(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a GLB file containing wheel-rotation-axis arrows and porous-flow-axis arrows."""
    glb_bytes = configuration_service.get_axes_glb(db, case_id, run_id)
    return Response(content=glb_bytes, media_type="model/gltf-binary")


@router.get("/cases/{case_id}/runs/{run_id}/overlay")
def get_run_overlay(
    case_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return OverlayData for a ready Run — parsed from its generated XML."""
    return configuration_service.get_run_overlay(db, case_id, run_id)


@router.get("/cases/{case_id}/compare", response_model=CaseCompareResult)
def compare_cases(
    case_id: str,
    with_case: str = Query(..., alias="with", description="ID of the case to compare against"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two cases: template settings diff, map conditions diff, assembly parts diff."""
    return configuration_service.compare_cases(db, case_id, with_case)


# ---------------------------------------------------------------------------
# Diff endpoint
# ---------------------------------------------------------------------------

@router.get("/runs/diff", response_model=DiffResult)
def diff_runs(
    a: str = Query(..., description="Run A ID"),
    b: str = Query(..., description="Run B ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return configuration_service.get_diff(db, a, b)
