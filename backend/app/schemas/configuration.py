from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.template_settings import RideHeightTemplateConfig


# ---------------------------------------------------------------------------
# Ride Height / Yaw config (stored in Condition)
# ---------------------------------------------------------------------------

class RideHeightConditionConfig(BaseModel):
    """Target ride height values per condition.

    The *how* (reference_parts, adjust_body_wheel_separately, use_original_wheel_position)
    now lives in Template.setup_option.ride_height (RideHeightTemplateConfig).
    """
    enabled: bool = False
    target_front_wheel_axis_rh: float | None = None  # m from ground
    target_rear_wheel_axis_rh: float | None = None   # m from ground
    # used when template.ride_height.adjust_body_wheel_separately=True and use_original_wheel_position=False
    target_front_wheel_rh: float | None = None
    target_rear_wheel_rh: float | None = None


class YawConditionConfig(BaseModel):
    center_mode: Literal["wheel_center", "user_input"] = "wheel_center"
    center_x: float = 0.0
    center_y: float = 0.0


# ---------------------------------------------------------------------------
# System (transform record)
# ---------------------------------------------------------------------------

class SystemCreate(BaseModel):
    name: str
    source_geometry_id: str
    condition_id: str | None = None
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    yaw_angle_deg: float = 0.0
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)


class SystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    source_geometry_id: str
    result_geometry_id: str | None
    condition_id: str | None
    transform_snapshot: dict | None
    created_by: str
    created_at: datetime


class TransformRequest(BaseModel):
    """POST /geometries/{id}/transform"""
    name: str  # name for the resulting Geometry
    condition_id: str | None = None
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    rh_template: RideHeightTemplateConfig = Field(default_factory=RideHeightTemplateConfig)
    yaw_angle_deg: float = 0.0
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)


# ---------------------------------------------------------------------------
# ConditionMap
# ---------------------------------------------------------------------------

class ConditionMapFolderCreate(BaseModel):
    name: str
    description: str | None = None


class ConditionMapFolderUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ConditionMapFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ConditionMapCreate(BaseModel):
    name: str
    description: str | None = None


class ConditionMapUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    folder_id: str | None = None


class ConditionMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None
    folder_id: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    condition_count: int = 0


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------

class ConditionCreate(BaseModel):
    name: str
    inflow_velocity: float
    yaw_angle: float = 0.0
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Condition name must not be empty")
        return v.strip()


class ConditionUpdate(BaseModel):
    name: str | None = None
    inflow_velocity: float | None = None
    yaw_angle: float | None = None
    ride_height: RideHeightConditionConfig | None = None
    yaw_config: YawConditionConfig | None = None


class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    map_id: str
    name: str
    inflow_velocity: float
    yaw_angle: float
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)
    created_by: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _parse_json_fields(cls, data):
        """Parse ride_height and yaw_config from ORM dict properties."""
        if hasattr(data, "__dict__"):
            rh = getattr(data, "ride_height", None)
            yc = getattr(data, "yaw_config", None)
            if isinstance(rh, dict):
                object.__setattr__(data, "_ride_height_parsed", rh)
            if isinstance(yc, dict):
                object.__setattr__(data, "_yaw_config_parsed", yc)
        return data

    @model_validator(mode="after")
    def _apply_parsed(self):
        if hasattr(self, "_ride_height_parsed"):
            try:
                self.ride_height = RideHeightConditionConfig(**self._ride_height_parsed)
            except Exception:
                pass
        if hasattr(self, "_yaw_config_parsed"):
            try:
                self.yaw_config = YawConditionConfig(**self._yaw_config_parsed)
            except Exception:
                pass
        return self


# ---------------------------------------------------------------------------
# Case
# ---------------------------------------------------------------------------

class CaseFolderCreate(BaseModel):
    name: str
    description: str | None = None


class CaseFolderUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CaseFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    name: str
    description: str | None = None
    template_id: str
    assembly_id: str
    map_id: str | None = None


class CaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_id: str | None = None
    assembly_id: str | None = None
    map_id: str | None = None
    folder_id: str | None = None
    parent_case_id: str | None = None  # set/clear parent case link


class CaseDuplicateRequest(BaseModel):
    name: str
    description: str | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_number: str = ""
    name: str
    description: str | None
    template_id: str
    assembly_id: str
    map_id: str | None
    folder_id: str | None = None
    parent_case_id: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    run_count: int = 0
    # Populated in router/service (not ORM columns)
    template_name: str = ""
    assembly_name: str = ""
    map_name: str = ""
    parent_case_number: str = ""
    parent_case_name: str = ""


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

class RunCreate(BaseModel):
    name: str = ""  # If empty, auto-generated as {case_number}_{run_number}_{condition_name}[_{comment}]
    condition_id: str
    comment: str = ""  # Optional suffix appended to auto-generated name


class RunUpdate(BaseModel):
    """Partial update for a Run. Only provided fields are updated."""
    geometry_override_id: str | None = None  # set/clear geometry override


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    run_number: str = ""
    name: str
    case_id: str
    condition_id: str
    xml_path: str | None
    stl_path: str | None = None
    geometry_override_id: str | None = None
    status: Literal["pending", "generating", "ready", "error"]
    error_message: str | None
    scheduler_job_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    # Populated in router/service
    condition_name: str = ""
    condition_velocity: float = 0.0
    condition_yaw: float = 0.0
    needs_transform: bool = False      # True when condition has ride_height.enabled or yaw_angle != 0
    transform_applied: bool = False    # True when geometry_override_id is set


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

class DiffField(BaseModel):
    field: str
    run_a_value: str | None
    run_b_value: str | None


class DiffResult(BaseModel):
    run_a_id: str
    run_b_id: str
    changed_fields: list[DiffField]


# ---------------------------------------------------------------------------
# Case Compare
# ---------------------------------------------------------------------------

class PartsDiffResult(BaseModel):
    added: list[str]    # parts in compare case but not in base
    removed: list[str]  # parts in base case but not in compare
    common: list[str]


class CaseCompareResult(BaseModel):
    base_case_id: str
    compare_case_id: str
    base_case_number: str = ""
    compare_case_number: str = ""
    template_settings_diff: list[DiffField]
    map_diff: list[DiffField]
    parts_diff: PartsDiffResult


# ---------------------------------------------------------------------------
# Sync Runs Preview (map change)
# ---------------------------------------------------------------------------

class SyncRunsPreviewItem(BaseModel):
    """One row in the sync preview: a condition that will be kept, added, or orphaned."""
    condition_id: str
    condition_name: str
    inflow_velocity: float
    yaw_angle: float
    action: Literal["keep", "add", "orphan"]
    existing_run_id: str | None = None  # set for keep/orphan
    existing_run_status: str | None = None


class SyncRunsPreview(BaseModel):
    """Preview of what will happen when a Case's map_id changes."""
    keep: list[SyncRunsPreviewItem]
    add: list[SyncRunsPreviewItem]
    orphan: list[SyncRunsPreviewItem]
