from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session, selectinload

from app.models.template import Template, TemplateVersion
from app.models.user import User
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateVersionCreate, TemplateVersionUpdate,
    TemplateForkRequest, SettingsValidateResponse, SettingsValidationError,
)
from app.schemas.template_settings import TemplateSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Settings validation
# ---------------------------------------------------------------------------

def validate_settings(data: dict) -> SettingsValidateResponse:
    """Validate raw dict against TemplateSettings schema using Pydantic."""
    try:
        normalized = TemplateSettings.model_validate(data)
        return SettingsValidateResponse(
            valid=True,
            normalized=normalized.model_dump(mode="json"),
        )
    except ValidationError as e:
        errors = [
            SettingsValidationError(
                field=".".join(str(loc) for loc in err["loc"]),
                message=err["msg"],
            )
            for err in e.errors()
        ]
        return SettingsValidateResponse(valid=False, errors=errors)


def _check_owner_or_admin(template: Template, current_user: User) -> None:
    if template.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")


def _get_template_or_404(db: Session, template_id: str) -> Template:
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


def _get_version_or_404(db: Session, template_id: str, version_id: str) -> TemplateVersion:
    version = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.id == version_id,
            TemplateVersion.template_id == template_id,
        )
    )
    if not version:
        raise HTTPException(status_code=404, detail="Template version not found")
    return version


# ---------------------------------------------------------------------------
# Template CRUD
# ---------------------------------------------------------------------------

def list_templates(db: Session, current_user: User) -> list[Template]:
    stmt = (
        select(Template)
        .options(selectinload(Template.versions))
        .order_by(Template.created_at.desc())
    )
    if not current_user.is_admin:
        stmt = stmt.where(Template.is_hidden == False)  # noqa: E712
    templates = db.scalars(stmt).all()
    return list(templates)


def toggle_hidden(
    db: Session, template_id: str, is_hidden: bool, current_user: User
) -> Template:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    template = _get_template_or_404(db, template_id)
    template.is_hidden = is_hidden
    db.commit()
    db.refresh(template)
    return template


def get_template(db: Session, template_id: str) -> Template:
    template = db.scalar(
        select(Template)
        .options(selectinload(Template.versions))
        .where(Template.id == template_id)
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


def create_template(
    db: Session, data: TemplateCreate, current_user: User
) -> Template:
    # name uniqueness is enforced by DB unique constraint, but give a clear error
    existing = db.scalar(select(Template).where(Template.name == data.name))
    if existing:
        raise HTTPException(status_code=409, detail="Template name already exists")

    template = Template(
        name=data.name,
        description=data.description,
        sim_type=data.sim_type,
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()  # generate template.id before creating version

    version = TemplateVersion(
        template_id=template.id,
        version_number=1,
        settings=data.settings.model_dump_json(),
        is_active=True,
        comment=data.comment,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session, template_id: str, data: TemplateUpdate, current_user: User
) -> Template:
    template = _get_template_or_404(db, template_id)
    _check_owner_or_admin(template, current_user)

    if data.name is not None:
        # check uniqueness
        existing = db.scalar(
            select(Template).where(Template.name == data.name, Template.id != template_id)
        )
        if existing:
            raise HTTPException(status_code=409, detail="Template name already exists")
        template.name = data.name
    if data.description is not None:
        template.description = data.description

    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: str, current_user: User) -> None:
    template = _get_template_or_404(db, template_id)
    _check_owner_or_admin(template, current_user)
    db.delete(template)
    db.commit()


# ---------------------------------------------------------------------------
# Version management
# ---------------------------------------------------------------------------

def list_versions(db: Session, template_id: str) -> list[TemplateVersion]:
    _get_template_or_404(db, template_id)
    versions = db.scalars(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version_number.asc())
    ).all()
    return list(versions)


def create_version(
    db: Session,
    template_id: str,
    data: TemplateVersionCreate,
    current_user: User,
) -> TemplateVersion:
    template = _get_template_or_404(db, template_id)
    _check_owner_or_admin(template, current_user)

    next_number = (
        db.scalar(
            select(func.max(TemplateVersion.version_number)).where(
                TemplateVersion.template_id == template_id
            )
        )
        or 0
    ) + 1

    # deactivate all existing versions
    db.execute(
        update(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .values(is_active=False)
    )

    version = TemplateVersion(
        template_id=template_id,
        version_number=next_number,
        settings=data.settings.model_dump_json(),
        is_active=True,
        comment=data.comment,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def activate_version(
    db: Session,
    template_id: str,
    version_id: str,
    current_user: User,
) -> TemplateVersion:
    template = _get_template_or_404(db, template_id)
    _check_owner_or_admin(template, current_user)

    version = _get_version_or_404(db, template_id, version_id)

    # deactivate all, then activate the target
    db.execute(
        update(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .values(is_active=False)
    )
    version.is_active = True
    db.commit()
    db.refresh(version)
    return version


def update_version_settings(
    db: Session,
    template_id: str,
    version_id: str,
    data: TemplateVersionUpdate,
    current_user: User,
) -> TemplateVersion:
    """Overwrite the settings (and optionally comment) of an existing version in-place."""
    template = _get_template_or_404(db, template_id)
    _check_owner_or_admin(template, current_user)
    version = _get_version_or_404(db, template_id, version_id)
    version.settings = data.settings.model_dump_json()
    if data.comment is not None:
        version.comment = data.comment
    db.commit()
    db.refresh(version)
    return version


def fork_template(
    db: Session,
    source_template_id: str,
    data: TemplateForkRequest,
    current_user: User,
) -> Template:
    """アクティブバージョンの設定をコピーして新しいテンプレートを作成する。"""
    source = get_template(db, source_template_id)

    existing = db.scalar(select(Template).where(Template.name == data.name))
    if existing:
        raise HTTPException(status_code=409, detail="Template name already exists")

    # アクティブバージョンの settings を引き継ぐ。なければ最新を使う。
    source_version = next((v for v in source.versions if v.is_active), None)
    if source_version is None:
        source_version = max(source.versions, key=lambda v: v.version_number, default=None)
    if source_version is None:
        raise HTTPException(status_code=400, detail="Source template has no versions")

    new_template = Template(
        name=data.name,
        description=data.description,
        sim_type=source.sim_type,
        created_by=current_user.id,
    )
    db.add(new_template)
    db.flush()

    comment = data.comment or f"Forked from '{source.name}' v{source_version.version_number}"
    new_version = TemplateVersion(
        template_id=new_template.id,
        version_number=1,
        settings=source_version.settings,  # JSON string をそのままコピー
        is_active=True,
        comment=comment,
        created_by=current_user.id,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_template)
    return new_template
