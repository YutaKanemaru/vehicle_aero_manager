"""
Geometry / GeometryAssembly のビジネスロジック。
"""
from __future__ import annotations

import logging
import os
import shutil
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


def _rmtree_force(path: Path) -> None:
    """shutil.rmtree with read-only override.

    Windows 環境では読み取り専用属性のファイルを rmtree しようとすると
    WinError 5 (アクセス拒否) が発生する。onerror で属性を解除してリトライする。
    """
    def _on_error(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    shutil.rmtree(path, onerror=_on_error)


from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.geometry import Geometry, GeometryAssembly, GeometryFolder, AssemblyFolder, assembly_geometry_link
from app.models.user import User
from app.models.configuration import Case
from app.models.system import System
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
    from sqlalchemy import select as _select
    from app.models.system import System
    # Exclude transform-result geometries (referenced as System.result_geometry_id)
    transform_ids_subq = _select(System.result_geometry_id).where(
        System.result_geometry_id.isnot(None)
    )
    return list(
        db.scalars(
            select(Geometry)
            .where(Geometry.id.not_in(transform_ids_subq))
            .order_by(Geometry.created_at.desc())
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
    decimation_ratio: float = 0.05,
) -> Geometry:
    geometry = Geometry(
        name=name,
        description=description,
        folder_id=folder_id,
        file_path="",           # 後で更新
        original_filename=file.filename or "unknown.stl",
        file_size=0,            # 後で更新
        status="pending",
        decimation_ratio=decimation_ratio,
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
        decimation_ratio=data.decimation_ratio,
        uploaded_by=current_user.id,
    )
    db.add(geometry)
    db.commit()
    db.refresh(geometry)
    return geometry


def run_analysis(db: Session, geometry_id: str, decimation_ratio: float = 0.05) -> None:
    """
    バックグラウンドタスクとして呼ばれる。
    STL を解析して analysis_result を更新する。
    - is_linked=False: file_path は upload_dir 相対パス
    - is_linked=True:  file_path はリンク先の絶対パス
    - decimation_ratio >= 1.0 の場合は GLB 変換をスキップ
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
        geometry.status = "ready-decimating"
        geometry.error_message = None
        db.commit()
    except Exception as exc:
        geometry.status = "error"
        geometry.error_message = str(exc)
        db.commit()
        return

    # decimation_ratio >= 1.0 の場合は GLB 変換をスキップ
    if decimation_ratio >= 1.0:
        geometry.status = "ready"
        db.commit()
        return

    # GLBキャッシュを事前生成
    import logging
    from app.services.viewer_service import build_viewer_glb
    try:
        build_viewer_glb(geometry, ratio=decimation_ratio)
    except Exception as exc:
        logging.getLogger(__name__).error(
            "GLB pre-build failed for geometry=%s ratio=%.3f: %s",
            geometry.id, decimation_ratio, exc,
            exc_info=True,
        )
        geometry.status = "error"
        geometry.error_message = f"GLB generation failed (ratio={decimation_ratio:.3f}): {exc}"
        db.commit()
        return

    geometry.status = "ready"
    geometry.error_message = None
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

    # Assembly に所属している場合は削除不可
    linked_count = db.scalar(
        select(func.count()).select_from(assembly_geometry_link).where(
            assembly_geometry_link.c.geometry_id == geometry_id
        )
    ) or 0
    if linked_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete geometry: it is linked to {linked_count} assembly(ies). "
                   "Remove it from all assemblies first.",
        )

    # System.source_geometry_id は NOT NULL のため削除不可。
    source_system_count = db.scalar(
        select(func.count()).select_from(System).where(
            System.source_geometry_id == geometry_id
        )
    ) or 0
    if source_system_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete geometry: it is used as source by {source_system_count} system(s). "
                   "Delete those systems first.",
        )

    # System.result_geometry_id は nullable なので NULL に更新してブロックを回避。
    result_systems = db.scalars(
        select(System).where(System.result_geometry_id == geometry_id)
    ).all()
    for sys in result_systems:
        sys.result_geometry_id = None
    if result_systems:
        db.flush()

    # アップロードファイルのみ削除。リンクの場合はリンク元ファイルは触れない。
    if not geometry.is_linked:
        try:
            fp = Path(geometry.file_path)
            # 絶対パスはそのまま、相対パスは upload_dir から解決
            resolved = fp if fp.is_absolute() else settings.upload_dir / fp
            upload_subdir = resolved.parent
            # upload_dir そのものを削除しないように安全ガード
            if upload_subdir.exists() and upload_subdir != settings.upload_dir:
                _rmtree_force(upload_subdir)
                logger.info("Deleted geometry files: %s", upload_subdir)
            else:
                logger.warning(
                    "Geometry file directory not found or unsafe path, skipping: %s", upload_subdir
                )
        except Exception as e:
            logger.warning("Failed to delete geometry files for %s: %s", geometry_id, e)
            # ファイル削除失敗でも DB 行は削除する

    # ビューワーキャッシュを削除
    try:
        from app.services.viewer_service import invalidate_cache
        invalidate_cache(geometry.id)
    except Exception:
        pass

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
    # Prevent deletion if Cases still reference this assembly
    linked_cases = db.query(Case).filter(Case.assembly_id == assembly_id).count()
    if linked_cases > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete assembly: {linked_cases} case(s) are still linked to it. "
                   "Delete or reassign those cases first.",
        )
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
