from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user, get_admin_user
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateVersionCreate,
    TemplateVersionResponse,
    TemplateForkRequest,
    SettingsValidateRequest,
    SettingsValidateResponse,
)
from app.schemas.template_settings import TemplateSettings, SIM_TYPE_PRESETS
from app.services import template_service

router = APIRouter()


def _build_response(template) -> TemplateResponse:
    """Attach active_version, version_count, and is_hidden to the response."""
    active = next((v for v in template.versions if v.is_active), None)
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        sim_type=template.sim_type,
        is_hidden=template.is_hidden,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
        active_version=TemplateVersionResponse.model_validate(active) if active else None,
        version_count=len(template.versions),
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[TemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    templates = template_service.list_templates(db, current_user)
    return [_build_response(t) for t in templates]


@router.post("/", response_model=TemplateResponse, status_code=201)
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = template_service.create_template(db, data, current_user)
    return _build_response(template)


# ---------------------------------------------------------------------------
# Validate settings — must be declared BEFORE /{template_id}
# ---------------------------------------------------------------------------

@router.post("/validate-settings", response_model=SettingsValidateResponse)
def validate_settings(
    body: SettingsValidateRequest,
    _: User = Depends(get_current_user),
):
    """Validate a raw settings dict against the TemplateSettings Pydantic schema."""
    return template_service.validate_settings(body.settings)


# ---------------------------------------------------------------------------
# Presets — must be declared BEFORE /{template_id} to avoid routing conflict
# ---------------------------------------------------------------------------

@router.get("/presets/{sim_type}", response_model=TemplateSettings)
def get_preset(
    sim_type: str,
    current_user: User = Depends(get_current_user),
):
    """Return a full TemplateSettings preset for the given sim_type.
    Valid values: 'aero', 'ghn', 'fan_noise'.
    """
    preset = SIM_TYPE_PRESETS.get(sim_type)
    if preset is None:
        raise HTTPException(
            status_code=404,
            detail=f"No preset for sim_type '{sim_type}'. Valid: {list(SIM_TYPE_PRESETS)}",
        )
    return preset


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = template_service.get_template(db, template_id)
    return _build_response(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = template_service.update_template(db, template_id, data, current_user)
    return _build_response(template)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template_service.delete_template(db, template_id, current_user)


@router.patch("/{template_id}/hide", response_model=TemplateResponse)
def set_template_hidden(
    template_id: str,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Admin-only: set or clear the is_hidden flag on a template."""
    if data.is_hidden is None:
        raise HTTPException(status_code=422, detail="is_hidden field is required")
    template = template_service.toggle_hidden(db, template_id, data.is_hidden, current_user)
    return _build_response(template)


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

@router.get("/{template_id}/versions", response_model=list[TemplateVersionResponse])
def list_versions(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return template_service.list_versions(db, template_id)


@router.post("/{template_id}/versions", response_model=TemplateVersionResponse, status_code=201)
def create_version(
    template_id: str,
    data: TemplateVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return template_service.create_version(db, template_id, data, current_user)


@router.patch("/{template_id}/versions/{version_id}/activate", response_model=TemplateVersionResponse)
def activate_version(
    template_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return template_service.activate_version(db, template_id, version_id, current_user)


# ---------------------------------------------------------------------------
# Fork
# ---------------------------------------------------------------------------

@router.post("/{template_id}/fork", response_model=TemplateResponse, status_code=201)
def fork_template(
    template_id: str,
    data: TemplateForkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """アクティブバージョンの設定をコピーして新しいテンプレートを作成する。"""
    template = template_service.fork_template(db, template_id, data, current_user)
    return _build_response(template)
