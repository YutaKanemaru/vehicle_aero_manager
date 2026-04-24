"""
Preview endpoints — overlay data for the Template Builder 3D viewer.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.schemas.overlay import OverlayData
from app.services import preview_service

router = APIRouter()


@router.get("/preview/overlay", response_model=OverlayData)
def get_overlay_data(
    template_id: str,
    assembly_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compute overlay data from Template + Assembly for the 3-D viewer.

    No XML file is written to disk — the solver deck is assembled in memory
    and overlay primitives are extracted from it.
    """
    return preview_service.compute_overlay_data(db, template_id, assembly_id)
