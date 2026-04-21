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
    ConditionCreate, ConditionResponse, ConditionUpdate,
    ConditionMapCreate, ConditionMapResponse, ConditionMapUpdate,
    DiffResult,
    RunCreate, RunResponse,
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


@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = configuration_service.get_case(db, case_id)
    return configuration_service.enrich_case_response(db, c)


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


@router.post("/cases/{case_id}/runs/{run_id}/generate", response_model=RunResponse)
def generate_xml(
    case_id: str,
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = configuration_service.trigger_xml_generation(
        db, case_id, run_id, current_user, background_tasks
    )
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
