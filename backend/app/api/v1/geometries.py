from fastapi import APIRouter, Depends, Form, Query, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.schemas.geometry import (
    GeometryResponse, GeometryUpdate, GeometryLinkRequest,
    GeometryFolderCreate, GeometryFolderUpdate, GeometryFolderResponse,
)
from app.schemas.configuration import TransformRequest
from app.services import geometry_service
from app.services import viewer_service
from app.services import ride_height_service

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
    decimation_ratio: float = Form(0.05),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """STL ファイルをアップロードする。解析はバックグラウンドで自動実行。"""
    geometry = geometry_service.upload_geometry(
        db, name, description, file, current_user, folder_id=folder_id
    )
    background_tasks.add_task(geometry_service.run_analysis, db, geometry.id, decimation_ratio)
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
    background_tasks.add_task(geometry_service.run_analysis, db, geometry.id, data.decimation_ratio)
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


@router.get("/{geometry_id}/file")
def download_geometry_file(
    geometry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """元のSTLファイルをダウンロードする。"""
    geometry = geometry_service.get_geometry(db, geometry_id)
    if geometry.is_linked:
        stl_path = geometry.file_path
    else:
        stl_path = str(settings.upload_dir / geometry.file_path)
    import os
    if not os.path.exists(stl_path):
        raise HTTPException(status_code=404, detail="STL file not found on server")
    return FileResponse(
        path=stl_path,
        media_type="model/stl",
        filename=geometry.original_filename or "geometry.stl",
    )


@router.get("/{geometry_id}/glb")
def get_geometry_glb(
    geometry_id: str,
    ratio: float = Query(0.05, ge=0.01, le=1.0, description="Keep ratio (0.01–1.0). e.g. 0.5 = keep 50%"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """STLをデシメーションしたGLBファイルを返す。初回は生成してキャッシュする。"""
    geometry = geometry_service.get_geometry(db, geometry_id)
    if geometry.status != "ready":
        raise HTTPException(status_code=400, detail="Geometry analysis not complete")

    # キャッシュ確認
    cached = viewer_service.get_cached_glb(geometry_id, ratio)
    if cached is not None:
        return Response(content=cached, media_type="model/gltf-binary")

    # キャッシュなし → 生成
    try:
        from app.models.geometry import Geometry
        db_geometry = db.get(Geometry, geometry_id)
        glb_bytes = viewer_service.build_viewer_glb(db_geometry, ratio=ratio)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GLB generation failed: {e}")

    return Response(content=glb_bytes, media_type="model/gltf-binary")


# ─── Ride Height / Yaw Transform ─────────────────────────────────────────────

@router.post("/{geometry_id}/transform", status_code=201)
def transform_geometry(
    geometry_id: str,
    data: TransformRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply ride height + yaw transform to an STL, producing a new Geometry + System record."""

    geometry = geometry_service.get_geometry(db, geometry_id)
    if geometry.status != "ready":
        raise HTTPException(status_code=400, detail="Geometry analysis not complete")
    if geometry.analysis_result is None:
        raise HTTPException(status_code=400, detail="Geometry has no analysis result")

    analysis_result = geometry.analysis_result  # already parsed by field_validator

    # Compute transform
    transform_snapshot = ride_height_service.compute_transform(
        analysis_result=analysis_result,
        rh_cfg=data.ride_height,
        yaw_angle_deg=data.yaw_angle_deg,
        yaw_cfg=data.yaw_config,
        rh_template_cfg=data.rh_template,
    )

    # Create System + new Geometry
    system, geom = ride_height_service.create_system_and_geometry(
        db=db,
        source_geometry=geometry,
        transform_snapshot=transform_snapshot,
        name=data.name,
        current_user=current_user,
        condition_id=data.condition_id,
        background_tasks=background_tasks,
    )

    import json
    snap = None
    if system.transform_snapshot:
        try:
            snap = json.loads(system.transform_snapshot)
        except Exception:
            snap = None

    return {
        "system_id": system.id,
        "geometry_id": geom.id,
        "geometry_name": geom.name,
        "geometry_status": geom.status,
        "transform_snapshot": snap,
    }
