from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.schemas.geometry import (
    AssemblyResponse, AssemblyCreate, AssemblyUpdate,
    AssemblyFolderCreate, AssemblyFolderUpdate, AssemblyFolderResponse,
)
from app.services import geometry_service

router = APIRouter()


# ─── Assembly Folder endpoints (must come before /{assembly_id}) ───────────────

@router.get("/folders/", response_model=list[AssemblyFolderResponse])
def list_assembly_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.list_assembly_folders(db)


@router.post("/folders/", response_model=AssemblyFolderResponse, status_code=201)
def create_assembly_folder(
    data: AssemblyFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.create_assembly_folder(db, data, current_user)


@router.patch("/folders/{folder_id}", response_model=AssemblyFolderResponse)
def update_assembly_folder(
    folder_id: str,
    data: AssemblyFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.update_assembly_folder(db, folder_id, data, current_user)


@router.delete("/folders/{folder_id}", status_code=204)
def delete_assembly_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    geometry_service.delete_assembly_folder(db, folder_id, current_user)


# ─── Assembly endpoints ────────────────────────────────────────────────────────────


@router.get("/", response_model=list[AssemblyResponse])
def list_assemblies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.list_assemblies(db)


@router.post("/", response_model=AssemblyResponse, status_code=201)
def create_assembly(
    data: AssemblyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.create_assembly(db, data, current_user)


@router.get("/{assembly_id}", response_model=AssemblyResponse)
def get_assembly(
    assembly_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.get_assembly(db, assembly_id)


@router.patch("/{assembly_id}", response_model=AssemblyResponse)
def update_assembly(
    assembly_id: str,
    data: AssemblyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.update_assembly(db, assembly_id, data, current_user)


@router.delete("/{assembly_id}", status_code=204)
def delete_assembly(
    assembly_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    geometry_service.delete_assembly(db, assembly_id, current_user)


@router.post("/{assembly_id}/geometries/{geometry_id}", response_model=AssemblyResponse)
def add_geometry(
    assembly_id: str,
    geometry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.add_geometry_to_assembly(db, assembly_id, geometry_id, current_user)


@router.delete("/{assembly_id}/geometries/{geometry_id}", response_model=AssemblyResponse)
def remove_geometry(
    assembly_id: str,
    geometry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geometry_service.remove_geometry_from_assembly(db, assembly_id, geometry_id, current_user)
