"""
Geometry / GeometryAssembly のビジネスロジック。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.geometry import Geometry, GeometryAssembly, GeometryFolder, AssemblyFolder
from app.models.user import User
from app.schemas.geometry import (
    AssemblyCreate, AssemblyUpdate,
    AssemblyFolderCreate, AssemblyFolderUpdate,
    GeometryFolderCreate, GeometryFolderUpdate, GeometryUpdate, GeometryLinkRequest,
)
from app.services.compute_engine import analyze_stl_to_json


# ─── helpers ─────────────────────────────────────────────────────────────────

def _check_owner_or_admin(resource_uploaded_by: str, current_user: User) -> None:
    if resource_uploaded_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")


def _geometry_or_404(db: Session, geometry_id: str) -> Geometry:
    g = db.get(Geometry, geometry_id)
    if not g:
        raise HTTPException(status_code=404, detail="Geometry not found")
    return g


def _assembly_or_404(db: Session, assembly_id: str) -> GeometryAssembly:
    a = db.scalar(
        select(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .where(GeometryAssembly.id == assembly_id)
    )
    if not a:
        raise HTTPException(status_code=404, detail="GeometryAssembly not found")
    return a


def _assembly_folder_or_404(db: Session, folder_id: str) -> AssemblyFolder:
    f = db.get(AssemblyFolder, folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="Assembly folder not found")
    return f


def _folder_or_404(db: Session, folder_id: str) -> GeometryFolder:
    f = db.get(GeometryFolder, folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")
    return f


def _geometry_upload_dir(geometry_id: str) -> Path:
    d = settings.upload_dir / "geometries" / geometry_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── Geometry CRUD ────────────────────────────────────────────────────────────

def list_geometries(db: Session) -> list[Geometry]:
    return list(
        db.scalars(
            select(Geometry).order_by(Geometry.created_at.desc())
        ).all()
    )


def get_geometry(db: Session, geometry_id: str) -> Geometry:
    return _geometry_or_404(db, geometry_id)


def upload_geometry(
    db: Session,
    name: str,
    description: str | None,
    file: UploadFile,
    current_user: User,
    folder_id: str | None = None,
) -> Geometry:
    geometry = Geometry(
        name=name,
        description=description,
        folder_id=folder_id,
        file_path="",           # 後で更新
        original_filename=file.filename or "unknown.stl",
        file_size=0,            # 後で更新
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(geometry)
    db.flush()  # id を確定

    # ファイル保存
    save_dir = _geometry_upload_dir(geometry.id)
    save_path = save_dir / (file.filename or "upload.stl")
    with save_path.open("wb") as _f:
        shutil.copyfileobj(file.file, _f, length=8 * 1024 * 1024)

    # 相対パスを保存（upload_dir からの相対）
    geometry.file_path = str(save_path.relative_to(settings.upload_dir))
    geometry.file_size = save_path.stat().st_size

    db.commit()
    db.refresh(geometry)
    return geometry


def link_geometry(
    db: Session,
    data: GeometryLinkRequest,
    current_user: User,
) -> Geometry:
    """
    ファイルをコピーせずパスのみ DB に登録する（Link only モード）。
    file_path はサーバーから読めるファイルシステムパスであること。
    解析は呼び出し元で BackgroundTasks に追加すること。
    """
    src = Path(data.file_path)
    if not src.exists():
        raise HTTPException(status_code=400, detail=f"File not found: {data.file_path}")
    if not src.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {data.file_path}")

    geometry = Geometry(
        name=data.name,
        description=data.description,
        folder_id=data.folder_id,
        file_path=str(src.resolve()),   # 絶対パスで保存
        original_filename=src.name,
        file_size=src.stat().st_size,
        is_linked=True,
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(geometry)
    db.commit()
    db.refresh(geometry)
    return geometry


def run_analysis(db: Session, geometry_id: str) -> None:
    """
    バックグラウンドタスクとして呼ばれる。
    STL を解析して analysis_result を更新する。
    - is_linked=False: file_path は upload_dir 相対パス
    - is_linked=True:  file_path はリンク先の絶対パス
    """
    geometry = db.get(Geometry, geometry_id)
    if not geometry:
        return  # already deleted

    geometry.status = "analyzing"
    db.commit()

    try:
        if geometry.is_linked:
            file_path = Path(geometry.file_path)
        else:
            file_path = settings.upload_dir / geometry.file_path
        result_json = analyze_stl_to_json(file_path)
        geometry.analysis_result = result_json
        geometry.status = "ready"
        geometry.error_message = None
    except Exception as exc:
        geometry.status = "error"
        geometry.error_message = str(exc)

    db.commit()


def update_geometry(
    db: Session,
    geometry_id: str,
    data: GeometryUpdate,
    current_user: User,
) -> Geometry:
    geometry = _geometry_or_404(db, geometry_id)
    _check_owner_or_admin(geometry.uploaded_by, current_user)
    if data.name is not None:
        geometry.name = data.name
    if data.description is not None:
        geometry.description = data.description
    # folder_id は明示的に指定された場合のみ更新（None でフォルダから外す）
    if "folder_id" in data.model_fields_set:
        if data.folder_id is not None:
            _folder_or_404(db, data.folder_id)  # 存在確認
        geometry.folder_id = data.folder_id
    db.commit()
    db.refresh(geometry)
    return geometry


def delete_geometry(db: Session, geometry_id: str, current_user: User) -> None:
    geometry = _geometry_or_404(db, geometry_id)
    _check_owner_or_admin(geometry.uploaded_by, current_user)

    # アップロードファイルのみ削除。リンクの場合はリンク元ファイルは触れない。
    if not geometry.is_linked:
        try:
            file_path = settings.upload_dir / geometry.file_path
            upload_subdir = file_path.parent
            if upload_subdir.exists():
                shutil.rmtree(upload_subdir)
        except Exception:
            pass  # ファイルが消えていても DB からは削除する

    db.delete(geometry)
    db.commit()


# ─── GeometryFolder CRUD ────────────────────────────────────────────────

def list_folders(db: Session) -> list[GeometryFolder]:
    return list(
        db.scalars(
            select(GeometryFolder).order_by(GeometryFolder.created_at.desc())
        ).all()
    )


def create_folder(
    db: Session, data: GeometryFolderCreate, current_user: User
) -> GeometryFolder:
    folder = GeometryFolder(
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_folder(
    db: Session, folder_id: str, data: GeometryFolderUpdate, current_user: User
) -> GeometryFolder:
    folder = _folder_or_404(db, folder_id)
    _check_owner_or_admin(folder.created_by, current_user)
    if data.name is not None:
        folder.name = data.name
    if data.description is not None:
        folder.description = data.description
    db.commit()
    db.refresh(folder)
    return folder


def delete_folder(db: Session, folder_id: str, current_user: User) -> None:
    folder = _folder_or_404(db, folder_id)
    _check_owner_or_admin(folder.created_by, current_user)
    # フォルダ内の Geometry は folder_id を null にリセット（未分類に移動）
    for g in folder.geometries:
        g.folder_id = None
    db.delete(folder)
    db.commit()


# ─── AssemblyFolder CRUD ───────────────────────────────────────────────

def list_assembly_folders(db: Session) -> list[AssemblyFolder]:
    return list(
        db.scalars(
            select(AssemblyFolder).order_by(AssemblyFolder.created_at.desc())
        ).all()
    )


def create_assembly_folder(
    db: Session, data: AssemblyFolderCreate, current_user: User
) -> AssemblyFolder:
    folder = AssemblyFolder(
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_assembly_folder(
    db: Session, folder_id: str, data: AssemblyFolderUpdate, current_user: User
) -> AssemblyFolder:
    folder = _assembly_folder_or_404(db, folder_id)
    _check_owner_or_admin(folder.created_by, current_user)
    if data.name is not None:
        folder.name = data.name
    if data.description is not None:
        folder.description = data.description
    db.commit()
    db.refresh(folder)
    return folder


def delete_assembly_folder(db: Session, folder_id: str, current_user: User) -> None:
    folder = _assembly_folder_or_404(db, folder_id)
    _check_owner_or_admin(folder.created_by, current_user)
    # フォルダ内の Assembly は folder_id を null にリセット（未分類に移動）
    for a in folder.assemblies:
        a.folder_id = None
    db.delete(folder)
    db.commit()


# ─── GeometryAssembly CRUD ───────────────────────────────────────────────────

def list_assemblies(db: Session) -> list[GeometryAssembly]:
    return list(
        db.scalars(
            select(GeometryAssembly)
            .options(selectinload(GeometryAssembly.geometries))
            .order_by(GeometryAssembly.created_at.desc())
        ).all()
    )


def get_assembly(db: Session, assembly_id: str) -> GeometryAssembly:
    return _assembly_or_404(db, assembly_id)


def create_assembly(
    db: Session, data: AssemblyCreate, current_user: User
) -> GeometryAssembly:
    assembly = GeometryAssembly(
        name=data.name,
        description=data.description,
        template_id=data.template_id,
        folder_id=data.folder_id,
        created_by=current_user.id,
    )
    db.add(assembly)
    db.commit()
    db.refresh(assembly)
    return assembly


def update_assembly(
    db: Session, assembly_id: str, data: AssemblyUpdate, current_user: User
) -> GeometryAssembly:
    assembly = _assembly_or_404(db, assembly_id)
    _check_owner_or_admin(assembly.created_by, current_user)
    if data.name is not None:
        assembly.name = data.name
    if data.description is not None:
        assembly.description = data.description
    if data.template_id is not None:
        assembly.template_id = data.template_id
    # folder_id: None は「フォルダから外す」を意味する。model_fields_set で判定。
    if "folder_id" in data.model_fields_set:
        if data.folder_id is not None:
            _assembly_folder_or_404(db, data.folder_id)
        assembly.folder_id = data.folder_id
    db.commit()
    db.refresh(assembly)
    return assembly


def delete_assembly(db: Session, assembly_id: str, current_user: User) -> None:
    assembly = _assembly_or_404(db, assembly_id)
    _check_owner_or_admin(assembly.created_by, current_user)
    db.delete(assembly)
    db.commit()


def add_geometry_to_assembly(
    db: Session, assembly_id: str, geometry_id: str, current_user: User
) -> GeometryAssembly:
    assembly = _assembly_or_404(db, assembly_id)
    _check_owner_or_admin(assembly.created_by, current_user)
    geometry = _geometry_or_404(db, geometry_id)

    if geometry not in assembly.geometries:
        assembly.geometries.append(geometry)
        db.commit()
        db.refresh(assembly)
    return assembly


def remove_geometry_from_assembly(
    db: Session, assembly_id: str, geometry_id: str, current_user: User
) -> GeometryAssembly:
    assembly = _assembly_or_404(db, assembly_id)
    _check_owner_or_admin(assembly.created_by, current_user)
    geometry = _geometry_or_404(db, geometry_id)

    if geometry in assembly.geometries:
        assembly.geometries.remove(geometry)
        db.commit()
        db.refresh(assembly)
    return assembly
