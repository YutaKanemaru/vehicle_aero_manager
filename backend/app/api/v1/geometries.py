from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.schemas.geometry import GeometryResponse, GeometryUpdate
from app.services import geometry_service

router = APIRouter()


# ─── Geometry ────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[GeometryResponse])
def list_geometries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.list_geometries(db)


@router.post("/", response_model=GeometryResponse, status_code=201)
def upload_geometry(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """STL ファイルをアップロードする。解析はバックグラウンドで自動実行。"""
    geometry = geometry_service.upload_geometry(db, name, description, file, current_user)
    background_tasks.add_task(geometry_service.run_analysis, db, geometry.id)
    return geometry


@router.get("/{geometry_id}", response_model=GeometryResponse)
def get_geometry(
    geometry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.get_geometry(db, geometry_id)


@router.patch("/{geometry_id}", response_model=GeometryResponse)
def update_geometry(
    geometry_id: str,
    data: GeometryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.update_geometry(db, geometry_id, data, current_user)


@router.delete("/{geometry_id}", status_code=204)
def delete_geometry(
    geometry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    geometry_service.delete_geometry(db, geometry_id, current_user)
