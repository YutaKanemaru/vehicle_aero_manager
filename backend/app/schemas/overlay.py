"""
Overlay data schema — returned by the preview endpoint.

All coordinates are absolute (metres). Frontend renders them directly.
No multiplier / pattern-matching / bbox calculation on the client side.
"""

from pydantic import BaseModel


class OverlayBoxItem(BaseModel):
    """Axis-aligned wireframe box (domain, refinement, porous, partial-volume)."""
    name: str
    level: int | None = None
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    color: str | None = None          # e.g. "#aaaaff"
    category: str = "refinement"      # "domain" | "refinement" | "porous" | "partial_volume"


class OverlayPlaneItem(BaseModel):
    """Semi-transparent plane (TG, section-cut)."""
    name: str
    type: str                         # "tg_ground" | "tg_body" | "section_cut"
    position: list[float]             # [x, y, z]
    normal: list[float]               # [nx, ny, nz]
    width: float
    height: float
    color: str | None = None


class OverlayDomainPartItem(BaseModel):
    """domain_part_instance — belt patch / uFX_ground on the floor."""
    name: str
    location: str                     # "z_min" | "z_max" | …
    export_mesh: bool
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_position: float                 # resolved absolute Z coordinate
    color: str | None = None


class OverlayProbeItem(BaseModel):
    """Probe file — list of points."""
    name: str
    points: list[list[float]]         # [[x, y, z], …]
    radius: float


class OverlayRideHeightRef(BaseModel):
    """Ride height reference axis positions for the 3-D viewer."""
    reference_mode: str               # "wheel_axis" | "user_input"
    reference_z_front: float | None = None   # wheel axis Z (m)
    reference_z_rear:  float | None = None   # wheel axis Z (m)
    reference_x_front: float | None = None   # wheel axis X (m)
    reference_x_rear:  float | None = None   # wheel axis X (m)
    reference_parts: list[str] = []   # patterns used for detection (wheel_axis mode)


class OverlayPartsGroup(BaseModel):
    """One group of part-name patterns (Parts tab badges)."""
    label: str
    patterns: list[str]
    matched_parts: list[str]


class OverlayData(BaseModel):
    """Complete overlay payload for the 3-D viewer."""
    domain_box: OverlayBoxItem | None = None
    refinement_boxes: list[OverlayBoxItem] = []
    porous_boxes: list[OverlayBoxItem] = []
    partial_volume_boxes: list[OverlayBoxItem] = []
    domain_parts: list[OverlayDomainPartItem] = []
    tg_planes: list[OverlayPlaneItem] = []
    section_cut_planes: list[OverlayPlaneItem] = []
    probes: list[OverlayProbeItem] = []
    parts_groups: list[OverlayPartsGroup] = []
    ground_z: float = 0.0
    ride_height_ref: OverlayRideHeightRef | None = None
