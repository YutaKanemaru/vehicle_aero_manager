from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.template_settings import TemplateSettings


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class TemplateCreate(BaseModel):
    name: str
    description: str | None = None
    sim_type: Literal["aero", "ghn"]
    settings: TemplateSettings
    comment: str | None = None  # comment for the initial version


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TemplateVersionCreate(BaseModel):
    settings: TemplateSettings
    comment: str | None = None


class TemplateForkRequest(BaseModel):
    name: str
    description: str | None = None
    comment: str | None = None  # comment for the v1 of the new template


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    version_number: int
    settings: TemplateSettings
    is_active: bool
    comment: str | None
    created_by: str
    created_at: datetime

    @field_validator("settings", mode="before")
    @classmethod
    def parse_settings(cls, v: str | dict) -> TemplateSettings:
        """settings is stored as a JSON string in the DB."""
        if isinstance(v, str):
            import json
            return TemplateSettings.model_validate(json.loads(v))
        return TemplateSettings.model_validate(v)


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    sim_type: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    active_version: TemplateVersionResponse | None = None
    version_count: int = 0
