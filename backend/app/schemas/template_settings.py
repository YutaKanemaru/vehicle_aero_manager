"""
Pydantic schema for Template settings JSON.

The settings field stored in TemplateVersion follows 5 sections:
  - setup_option:         flags controlling computation behaviour and ground mode
  - simulation_parameter: fixed physical values and run time settings
  - setup:                geometry-relative sizing rules for mesh / BCs
  - output:               full data / partial surface / partial volume / coefficients / probes
  - target_names:         part-name matching patterns
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.ultrafluid.schema import (
    OutputVariablesFull,
    OutputVariablesSurface,
    PartialSurfaceOutputVariables,
    PartialVolumeOutputVariables,
    SectionCutOutputVariables,
)


# ---------------------------------------------------------------------------
# setup_option — simulation
# ---------------------------------------------------------------------------

class SimulationOption(BaseModel):
    temperature_degree: bool = True       # input temperature is °C (converted to K)
    simulation_time_with_FP: bool = False # use flow-passage time instead of fixed time


# ---------------------------------------------------------------------------
# setup_option — meshing
# ---------------------------------------------------------------------------

class TriangleSplittingInstanceConfig(BaseModel):
    name: str
    active: bool = True
    max_absolute_edge_length: float = 0.0
    max_relative_edge_length: float = 9.0
    parts: list[str] = Field(default_factory=list)


class MeshingOption(BaseModel):
    triangle_splitting: bool = True
    max_absolute_edge_length: float = 0.0
    max_relative_edge_length: float = 9.0
    refinement_level_transition_layers: int = 8
    domain_bounding_box_relative: bool = True  # bbox multipliers relative to car dimensions
    box_offset_relative: bool = True
    box_refinement_porous: bool = True
    triangle_splitting_instances: list[TriangleSplittingInstanceConfig] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# setup_option — boundary conditions: belt
# ---------------------------------------------------------------------------

class BeltSize(BaseModel):
    x: float
    y: float


class NarrowCarFallback(BaseModel):
    """Prevent wheel belts from crossing/overlapping on narrow cars."""
    enabled: bool = False
    min_belt_gap: float = 0.3  # m — minimum gap between LH and RH wheel belts


class Belt5Config(BaseModel):
    """Configuration for 5-belt system (2 front, 2 rear, 1 center)."""
    wheel_belt_location_auto: bool = True
    narrow_car_fallback: NarrowCarFallback = Field(default_factory=NarrowCarFallback)
    center_belt_position: Literal["at_wheelbase_center", "user_specified"] = "at_wheelbase_center"
    center_belt_x_pos: float | None = None        # used when center_belt_position == "user_specified"
    belt_size_wheel: BeltSize = Field(default_factory=lambda: BeltSize(x=0.4, y=0.3))
    belt_size_center: BeltSize = Field(default_factory=lambda: BeltSize(x=0.4, y=0.3))
    include_wheel_belt_forces: bool = True         # False → wheel belts added to passive_parts


class Belt1Config(BaseModel):
    """Configuration for single-belt system."""
    belt_size: BeltSize = Field(default_factory=lambda: BeltSize(x=0.4, y=1.2))


# ---------------------------------------------------------------------------
# setup_option — boundary conditions: boundary layer suction (no-slip xmin)
#
# Available for all ground_mode values EXCEPT "full_moving".
# Also available for ghn / fan_noise (same fields, no belt-based options).
#
# ground_mode == "rotating_belt_5":
#   no_slip_xmin_from_belt_xmin and bl_xmin_offset are active.
# All other modes (static / rotating_belt_1 / ghn / fan_noise):
#   User specifies no_slip_xmin_pos directly.
# ---------------------------------------------------------------------------

class BLSuctionConfig(BaseModel):
    apply: bool = True
    no_slip_xmin_pos: float | None = None          # direct user input (non-belt-5 modes)
    # 5-belt only:
    no_slip_xmin_from_belt_xmin: bool = True       # derive from center belt x_min
    bl_xmin_offset: float = 0.0                    # m — added to belt x_min when above is True


# ---------------------------------------------------------------------------
# setup_option — boundary conditions: ground
# ---------------------------------------------------------------------------

class GroundConfig(BaseModel):
    """
    Ground and wheel boundary condition settings.

    ground_mode is External Aero specific. For ghn / fan_noise:
      - wheels are always static (no-slip, no rotation)
      - ground is static
      - overset_wheels is ignored
      - belt configs are ignored
      Only bl_suction and ground_patch_active apply.
    """
    # Ground height definition
    ground_height_mode: Literal["from_geometry", "absolute"] = "from_geometry"
    ground_height_absolute: float = 0.0  # m — used when ground_height_mode == "absolute"
    # from_geometry 時に STL z_min に加算するオフセット (m)。例: +0.01 の場合 ground_height = z_min + 0.01
    ground_height_offset_from_geom_zMin: float = 0.0

    # aero: one of 4 exclusive modes
    ground_mode: Literal[
        "static", "rotating_belt_1", "rotating_belt_5", "full_moving"
    ] = "rotating_belt_5"

    # aero only — overset mesh for rotating wheels
    # full_moving also uses overset if true
    overset_wheels: bool = True

    # all modes except full_moving
    ground_patch_active: bool = True

    # Boundary layer suction — not available for full_moving
    bl_suction: BLSuctionConfig = Field(default_factory=BLSuctionConfig)

    # Belt configs — only one is active depending on ground_mode
    belt5: Belt5Config = Field(default_factory=Belt5Config)
    belt1: Belt1Config = Field(default_factory=Belt1Config)

    # Ground box refinement (aero only)
    # Automatically forced ON when enable_ground_tg is True
    apply_static_ground_refinement: bool = True


# ---------------------------------------------------------------------------
# setup_option — boundary conditions: turbulence generator (aero only)
# ---------------------------------------------------------------------------

class TurbulenceGeneratorOption(BaseModel):
    # Available for sim_type == "aero" regardless of ground_mode.
    # enable_ground_tg = True forces apply_static_ground_refinement ON in Compute Engine.
    enable_ground_tg: bool = True
    enable_body_tg: bool = True
    # Tunable parameters (Computed Engine uses these)
    ground_tg_num_eddies: int = 800
    ground_tg_intensity: float = 0.05
    body_tg_num_eddies: int = 800
    body_tg_intensity: float = 0.01


# ---------------------------------------------------------------------------
# setup_option — compute flags
# ---------------------------------------------------------------------------

class ComputeOption(BaseModel):
    """Controls which Computed blocks are generated. Config can override per-case.

    Removed flags (now auto-derived in compute_engine.assemble_ufx_solver_deck):
      rotate_wheels / moving_ground → derived from ground_mode
      porous_media   → derived from bool(template_settings.porous_coefficients)
      turbulence_generator → derived from tg_cfg.enable_ground_tg | enable_body_tg
    """
    adjust_ride_height: bool = False  # ride height adjustment (Config can override)


# ---------------------------------------------------------------------------
# setup_option — root
# ---------------------------------------------------------------------------

class BoundaryConditionOption(BaseModel):
    ground: GroundConfig = Field(default_factory=GroundConfig)
    turbulence_generator: TurbulenceGeneratorOption = Field(
        default_factory=TurbulenceGeneratorOption
    )


class SetupOption(BaseModel):
    simulation: SimulationOption = Field(default_factory=SimulationOption)
    meshing: MeshingOption = Field(default_factory=MeshingOption)
    boundary_condition: BoundaryConditionOption = Field(
        default_factory=BoundaryConditionOption
    )
    compute: ComputeOption = Field(default_factory=ComputeOption)


# ---------------------------------------------------------------------------
# simulation_parameter
# ---------------------------------------------------------------------------

class SimulationParameter(BaseModel):
    inflow_velocity: float = 38.88          # m/s
    density: float = 1.2041                 # kg/m³
    dynamic_viscosity: float = 1.8194e-5    # kg/(s·m)
    temperature: float = 20.0               # °C (converted to K if temperature_degree=True)
    specific_gas_constant: float = 287.05   # J/(kg·K)
    mach_factor: float = 2.0
    num_ramp_up_iter: int = 200
    # Mesh sizing — user inputs coarsest; UI shows finest = coarsest / 2^N
    coarsest_voxel_size: float = 0.192      # m (ext aero: 0.192, GHN: 0.256)
    number_of_resolution: int = 7           # ext aero: 7, GHN: 9
    # Run time (seconds) — Compute Engine converts to num_coarsest_iterations
    simulation_time: float = 2.0
    simulation_time_FP: float = 30.0        # flow passages (used if simulation_time_with_FP=True)
    start_averaging_time: float = 1.5       # seconds
    avg_window_size: float = 0.3            # seconds
    yaw_angle: float = 0.0                  # degrees — Template default (Config can override)


# ---------------------------------------------------------------------------
# setup — meshing
# ---------------------------------------------------------------------------

class BoxRefinement(BaseModel):
    level: int
    box: list[float] = Field(..., min_length=6, max_length=6)  # xmin,xmax,ymin,ymax,zmin,zmax
    mode: Literal["vehicle_bbox_factors", "user_defined"] = "vehicle_bbox_factors"
    # vehicle_bbox_factors: values are multipliers applied to vehicle dimensions (relative)
    # user_defined: values are absolute coordinates in metres


class BoxRefinementAroundParts(BaseModel):
    """Box refinement defined relative to matched parts' bounding box.
    Compute Engine resolves this to absolute coordinates at XML generation time.
    """
    level: int = 1
    parts: list[str]                    # part name patterns (substring match)
    offset_xmin: float = 0.5            # m — extend beyond matched bbox in -X direction
    offset_xmax: float = 0.5            # m — extend beyond matched bbox in +X direction
    offset_ymin: float = 0.5            # m — extend beyond matched bbox in -Y direction
    offset_ymax: float = 0.5            # m — extend beyond matched bbox in +Y direction
    offset_zmin: float = 0.5            # m — extend beyond matched bbox in -Z direction
    offset_zmax: float = 0.5            # m — extend beyond matched bbox in +Z direction


class OffsetRefinement(BaseModel):
    level: int
    normal_distance: float
    parts: list[str] = Field(default_factory=list)


class CustomRefinement(BaseModel):
    level: int
    parts: list[str]


class MeshingSetup(BaseModel):
    box_refinement: dict[str, BoxRefinement] = Field(default_factory=dict)
    part_box_refinement: dict[str, BoxRefinement] = Field(default_factory=dict)
    part_based_box_refinement: dict[str, BoxRefinementAroundParts] = Field(default_factory=dict)
    offset_refinement: dict[str, OffsetRefinement] = Field(default_factory=dict)
    custom_refinement: dict[str, CustomRefinement] = Field(default_factory=dict)


class Setup(BaseModel):
    # 6-element list: [x_min_f, x_max_f, y_min_f, y_max_f, z_min_f, z_max_f]
    # factors applied to vehicle bounding box edges:
    #   result[i] = factor[i] * body_dimension + bbox_edge[i]
    domain_bounding_box: list[float] = Field(
        default=[-5.0, 10.0, -12.0, 12.0, 0.0, 20.0],
        min_length=6,
        max_length=6,
    )
    meshing: MeshingSetup = Field(default_factory=MeshingSetup)


# ---------------------------------------------------------------------------
# output settings
# ---------------------------------------------------------------------------

class FullDataOutputConfig(BaseModel):
    """Full-volume and surface data output configuration."""
    output_start_time: float | None = None      # seconds; None = auto (= simulation_time)
    output_interval: float | None = None         # seconds; None = auto (= simulation_time)
    file_format_ensight: bool = False
    file_format_h3d: bool = True
    output_coarsening_active: bool = False
    coarsest_target_refinement_level: int = 3
    coarsen_by_num_refinement_levels: int = 0
    merge_output: bool = True
    delete_unmerged: bool = True
    output_variables_full: OutputVariablesFull = Field(default_factory=OutputVariablesFull)
    output_variables_surface: OutputVariablesSurface = Field(default_factory=OutputVariablesSurface)
    # bounding box for output volume
    bbox_mode: Literal["from_meshing_box", "user_defined"] = "from_meshing_box"
    bbox_source_box_name: str | None = None      # box name from meshing setup (bbox_mode == "from_meshing_box")
    bbox: list[float] | None = None              # [xmin,xmax,ymin,ymax,zmin,zmax] (bbox_mode == "user_defined")


class PartialSurfaceOutputConfig(BaseModel):
    """Partial surface export configuration (one instance)."""
    name: str = "partial_surface"
    output_start_time: float | None = None
    output_interval: float | None = None
    file_format_ensight: bool = False
    file_format_h3d: bool = True
    merge_output: bool = True
    delete_unmerged: bool = True
    include_parts: list[str] = Field(default_factory=list)
    exclude_parts: list[str] = Field(default_factory=list)
    output_variables: PartialSurfaceOutputVariables = Field(default_factory=PartialSurfaceOutputVariables)
    # None = no baffle auto-exclude; "front_only"/"back_only"/"both" = auto-exclude baffle
    baffle_export_option: Literal["front_only", "back_only", "both"] | None = None


class PartialVolumeOutputConfig(BaseModel):
    """Partial volume export configuration (one instance)."""
    name: str = "partial_volume"
    output_start_time: float | None = None
    output_interval: float | None = None
    file_format_ensight: bool = False
    file_format_h3d: bool = True
    output_coarsening_active: bool = False
    coarsest_target_refinement_level: int = 3
    coarsen_by_num_refinement_levels: int = 0
    merge_output: bool = True
    delete_unmerged: bool = True
    output_variables: PartialVolumeOutputVariables = Field(default_factory=PartialVolumeOutputVariables)
    # bounding box specification
    bbox_mode: Literal["from_meshing_box", "around_parts", "user_defined"] = "user_defined"
    bbox_source_box_name: str | None = None   # bbox_mode == "from_meshing_box"
    bbox_source_parts: list[str] = Field(default_factory=list)  # bbox_mode == "around_parts"
    bbox_offset_xmin: float = 0.0   # m — extend beyond parts bbox in -X (around_parts only)
    bbox_offset_xmax: float = 0.0   # m — extend beyond parts bbox in +X (around_parts only)
    bbox_offset_ymin: float = 0.0   # m — extend beyond parts bbox in -Y (around_parts only)
    bbox_offset_ymax: float = 0.0   # m — extend beyond parts bbox in +Y (around_parts only)
    bbox_offset_zmin: float = 0.0   # m — extend beyond parts bbox in -Z (around_parts only)
    bbox_offset_zmax: float = 0.0   # m — extend beyond parts bbox in +Z (around_parts only)
    bbox: list[float] | None = None           # [xmin,xmax,ymin,ymax,zmin,zmax] bbox_mode == "user_defined"


class AeroCoefficientsConfig(BaseModel):
    """Aero force/moment coefficient output settings (aero sim_type only)."""
    reference_area_auto: bool = True
    reference_area: float | None = None           # m² — used when reference_area_auto=False
    reference_length_auto: bool = True
    reference_length: float | None = None          # m — used when reference_length_auto=False
    # coefficients_along_axis
    coefficients_along_axis_active: bool = False
    num_sections_x: int = 100
    num_sections_y: int = 0
    num_sections_z: int = 0
    export_bounds_active: bool = True
    export_bounds_exclude_domain_parts: bool = True


class ProbePointConfig(BaseModel):
    """Single probe location for CSV export/import (x;y;z;description format)."""
    x_pos: float = 0.0
    y_pos: float = 0.0
    z_pos: float = 0.0
    description: str = ""


class ProbeFileOutputVariables(BaseModel):
    """Output variables for a probe_file_instance. None = use solver default."""
    pressure: bool | None = None
    time_avg_pressure: bool | None = None
    window_avg_pressure: bool | None = None
    cp: bool | None = None
    velocity: bool | None = None
    time_avg_velocity: bool | None = None
    window_avg_velocity: bool | None = None
    velocity_magnitude: bool | None = None
    time_avg_velocity_magnitude: bool | None = None
    window_avg_velocity_magnitude: bool | None = None
    wall_shear_stress: bool | None = None           # surface probes only
    time_avg_wall_shear_stress: bool | None = None  # surface probes only
    window_avg_wall_shear_stress: bool | None = None  # surface probes only
    density: bool | None = None
    time_avg_density: bool | None = None
    window_avg_density: bool | None = None
    pressure_std: bool | None = None
    pressure_var: bool | None = None


class ProbeFileConfig(BaseModel):
    """Configuration for one <probe_file_instance>."""
    name: str = "probe"
    probe_type: str = "volume"          # "volume" | "surface"
    radius: float = 0.0                 # m — fictitious sphere radius for averaging
    output_frequency: float = 1.0       # coarsest iterations between outputs
    output_start_iteration: int = 0
    scientific_notation: bool = True
    output_precision: int = 7
    output_variables: ProbeFileOutputVariables = Field(default_factory=ProbeFileOutputVariables)
    points: list[ProbePointConfig] = Field(default_factory=list)  # probe locations for CSV gen


class SectionCutConfig(BaseModel):
    """Section cut output configuration (one instance)."""
    name: str = "section_cut"
    output_start_time: float | None = None   # seconds; None = use full_data value
    output_interval: float | None = None      # seconds; None = use full_data value
    file_format_ensight: bool = False
    file_format_h3d: bool = True
    merge_output: bool = True
    delete_unmerged: bool = True
    triangulation: bool = False
    # Cut plane definition — axis normal direction (unit vector)
    axis_x: float = 0.0
    axis_y: float = 0.0
    axis_z: float = 1.0
    # Point on the cut plane
    point_x: float = 0.0
    point_y: float = 0.0
    point_z: float = 0.0
    # Optional bounding box [xmin,xmax,ymin,ymax,zmin,zmax]; empty = full domain
    bbox: list[float] = Field(default_factory=list)
    output_variables: SectionCutOutputVariables = Field(default_factory=SectionCutOutputVariables)


class OutputSettings(BaseModel):
    full_data: FullDataOutputConfig = Field(default_factory=FullDataOutputConfig)
    partial_surfaces: list[PartialSurfaceOutputConfig] = Field(default_factory=list)
    partial_volumes: list[PartialVolumeOutputConfig] = Field(default_factory=list)
    aero_coefficients: AeroCoefficientsConfig = Field(default_factory=AeroCoefficientsConfig)
    section_cuts: list[SectionCutConfig] = Field(default_factory=list)
    probe_files: list[ProbeFileConfig] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# porous_media — coefficients per porous part (multiple instances supported)
# ---------------------------------------------------------------------------

class PorousMedia(BaseModel):
    part_name: str              # must match a part name found in the assembly STL
    inertial_resistance: float  # 1/m
    viscous_resistance: float   # 1/s


# ---------------------------------------------------------------------------
# target_names
# ---------------------------------------------------------------------------

class TargetNames(BaseModel):
    # Generic part-name matching patterns (prefix/substring)
    wheel: list[str] = Field(default_factory=list)
    rim: list[str] = Field(default_factory=list)
    porous: list[str] = Field(default_factory=list)
    car_bounding_box: list[str] = Field(default_factory=list)
    baffle: list[str] = Field(default_factory=list)
    # windtunnel: excluded from offset refinement (unless manually specified) + passive parts
    windtunnel: list[str] = Field(default_factory=list)
    # Individual tyre part name patterns — required for OSM + belt auto-position (aero only)
    wheel_tire_fr_lh: str = ""
    wheel_tire_fr_rh: str = ""
    wheel_tire_rr_lh: str = ""
    wheel_tire_rr_rh: str = ""
    # OSM region part name patterns (aero + overset_wheels=True only)
    overset_fr_lh: str = ""
    overset_fr_rh: str = ""
    overset_rr_lh: str = ""
    overset_rr_rh: str = ""
    tire_roughness: float = 0.0            # m — applied to tyre wall BC roughness


# ---------------------------------------------------------------------------
# Root settings schema
# ---------------------------------------------------------------------------

def _aero_setup() -> Setup:
    """Default meshing setup for aero/fan_noise: 5 box zones + 2 offset layers."""
    _coarse = 0.192  # default coarsest_voxel_size
    _rl6_dist = _coarse * (0.5 ** 6) * 12   # = 0.036 m
    _rl7_dist = _coarse * (0.5 ** 7) * 8    # = 0.012 m
    return Setup(
        meshing=MeshingSetup(
            box_refinement={
                "Box_RL1": BoxRefinement(level=1, box=[-1.0,  3.0,   -1.0,   1.0,   -0.2, 1.5 ]),
                "Box_RL2": BoxRefinement(level=2, box=[-0.5,  1.5,   -0.75,  0.75,  -0.2, 1.0 ]),
                "Box_RL3": BoxRefinement(level=3, box=[-0.3,  1.0,   -0.5,   0.5,   -0.2, 0.75]),
                "Box_RL4": BoxRefinement(level=4, box=[-0.2,  0.6,   -0.3,   0.3,   -0.2, 0.5 ]),
                "Box_RL5": BoxRefinement(level=5, box=[-0.1,  0.3,   -0.15,  0.15,  -0.2, 0.25]),
            },
            offset_refinement={
                "Body_Offset_ALL_RL7": OffsetRefinement(level=7, normal_distance=_rl7_dist, parts=[]),
                "Body_Offset_ALL_RL6": OffsetRefinement(level=6, normal_distance=_rl6_dist, parts=[]),
            },
        )
    )


class TemplateSettings(BaseModel):
    setup_option: SetupOption = Field(default_factory=SetupOption)
    simulation_parameter: SimulationParameter = Field(default_factory=SimulationParameter)
    setup: Setup = Field(default_factory=_aero_setup)
    output: OutputSettings = Field(default_factory=OutputSettings)
    target_names: TargetNames = Field(default_factory=TargetNames)
    porous_coefficients: list[PorousMedia] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Sim-type presets — full TemplateSettings instances with per-type defaults
# ---------------------------------------------------------------------------

def _ghn_preset() -> TemplateSettings:
    """GHN preset: larger voxel, more resolution levels, no TG, static ground."""
    return TemplateSettings(
        simulation_parameter=SimulationParameter(
            coarsest_voxel_size=0.256,
            number_of_resolution=9,
        ),
        setup_option=SetupOption(
            meshing=MeshingOption(triangle_splitting=False),
            boundary_condition=BoundaryConditionOption(
                ground=GroundConfig(ground_mode="static"),
                turbulence_generator=TurbulenceGeneratorOption(
                    enable_ground_tg=False,
                    enable_body_tg=False,
                ),
            ),
        ),
    )


def _fan_noise_preset() -> TemplateSettings:
    """Fan noise preset: same mesh sizing as aero, TG disabled."""
    return TemplateSettings(
        setup_option=SetupOption(
            boundary_condition=BoundaryConditionOption(
                turbulence_generator=TurbulenceGeneratorOption(
                    enable_ground_tg=False,
                    enable_body_tg=False,
                ),
            ),
        ),
    )


SIM_TYPE_PRESETS: dict[str, TemplateSettings] = {
    "aero": TemplateSettings(),
    "ghn": _ghn_preset(),
    "fan_noise": _fan_noise_preset(),
}
