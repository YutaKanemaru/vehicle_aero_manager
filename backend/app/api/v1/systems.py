"""API endpoints for System (coordinate transform records)."""
import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.system import System
from app.models.user import User
from app.schemas.configuration import SystemResponse

router = APIRouter()


def _get_system_or_404(db: Session, system_id: str) -> System:
    system = db.get(System, system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


def _serialize(system: System) -> dict:
    snap = None
    if system.transform_snapshot:
        try:
            snap = json.loads(system.transform_snapshot)
        except Exception:
            snap = None
    return {
        "id": system.id,
        "name": system.name,
        "source_geometry_id": system.source_geometry_id,
        "result_geometry_id": system.result_geometry_id,
        "condition_id": system.condition_id,
        "transform_snapshot": snap,
        "created_by": system.created_by,
        "created_at": system.created_at,
    }


@router.get("/systems/", response_model=list[SystemResponse])
def list_systems(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    systems = list(db.scalars(select(System).order_by(System.created_at.desc())).all())
    return [_serialize(s) for s in systems]


@router.get("/systems/{system_id}", response_model=SystemResponse)
def get_system(
    system_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    system = _get_system_or_404(db, system_id)
    return _serialize(system)


@router.delete("/systems/{system_id}", status_code=204)
def delete_system(
    system_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    system = _get_system_or_404(db, system_id)
    if system.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Optionally delete result geometry (cascade handled by geometry_service)
    if system.result_geometry_id:
        from app.models.geometry import Geometry
        from app.services.geometry_service import delete_geometry
        geom = db.get(Geometry, system.result_geometry_id)
        if geom:
            try:
                delete_geometry(db, system.result_geometry_id, current_user)
            except Exception:
                pass  # geometry may already be deleted

    db.delete(system)
    db.commit()
    return Response(status_code=204)


@router.get("/systems/{system_id}/landmarks-glb")
def get_landmarks_glb(
    system_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a GLB visualising landmark points (before/after transform)."""
    system = _get_system_or_404(db, system_id)
    if not system.transform_snapshot:
        raise HTTPException(status_code=400, detail="System has no transform snapshot")

    snapshot = json.loads(system.transform_snapshot)
    from app.services.viewer_service import build_landmarks_glb
    try:
        glb_bytes = build_landmarks_glb(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(content=glb_bytes, media_type="model/gltf-binary")
