from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.schemas.geometry import (
    GeometryResponse, GeometryUpdate, GeometryLinkRequest,
    GeometryFolderCreate, GeometryFolderUpdate, GeometryFolderResponse,
)
from app.services import geometry_service

router = APIRouter()


# ─── Folders ─────────────────────────────────────────────────────────────────

@router.get("/folders/", response_model=list[GeometryFolderResponse])
def list_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.list_folders(db)


@router.post("/folders/", response_model=GeometryFolderResponse, status_code=201)
def create_folder(
    data: GeometryFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.create_folder(db, data, current_user)


@router.patch("/folders/{folder_id}", response_model=GeometryFolderResponse)
def update_folder(
    folder_id: str,
    data: GeometryFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.update_folder(db, folder_id, data, current_user)


@router.delete("/folders/{folder_id}", status_code=204)
def delete_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    geometry_service.delete_folder(db, folder_id, current_user)


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
    folder_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """STL ファイルをアップロードする。解析はバックグラウンドで自動実行。"""
    geometry = geometry_service.upload_geometry(
        db, name, description, file, current_user, folder_id=folder_id
    )
    background_tasks.add_task(geometry_service.run_analysis, db, geometry.id)
    return geometry


@router.post("/link", response_model=GeometryResponse, status_code=201)
def link_geometry(
    background_tasks: BackgroundTasks,
    data: GeometryLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    STL ファイルをコピーせずサーバーパスのみ登録（Link only モード）。
    file_path はバックエンドコンテナ内からアクセス可能なパスを指定すること。
    解析はアップロード時と同様に自動実行。
    """
    geometry = geometry_service.link_geometry(db, data, current_user)
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
