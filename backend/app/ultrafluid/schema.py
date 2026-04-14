"""
Pydantic v2 models for the Ultrafluid (uFX) solver deck XML schema.

Structure mirrors the <uFX_solver_deck> XML hierarchy exactly.
Field names match XML tag names (snake_case).

Field Classification:
  Fixed    - Stored in Template, does not change per geometry
  Computed - Derived from STL geometry (trimesh/numpy) in Compute Engine
  UserInput - Set by engineer via UI
"""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Common primitives
# ---------------------------------------------------------------------------

class XYZPos(BaseModel):
    """Used for positions: <x_pos>, <y_pos>, <z_pos>"""
    x_pos: float
    y_pos: float
    z_pos: float


class XYZDir(BaseModel):
    """Used for directions/velocities: <x_dir>, <y_dir>, <z_dir>"""
    x_dir: float
    y_dir: float
    z_dir: float


class BoundingBox(BaseModel):
    """6-sided axis-aligned bounding box used in multiple sections."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


class BoundingRange(BaseModel):
    """2D bounding range (x/y only) used in domain_part_instance."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class FileFormat(BaseModel):
    ensight: bool
    h3d: bool


class OutputCoarsening(BaseModel):
    active: bool
    coarsen_by_num_refinement_levels: int
    coarsest_target_refinement_level: int
    export_uncoarsened_voxels: bool


class ProbeOutputVariables(BaseModel):
    """Output variables applicable to probe_file_instance (volume or surface)."""
    pressure: Optional[bool] = None
    time_avg_pressure: Optional[bool] = None
    window_avg_pressure: Optional[bool] = None
    cp: Optional[bool] = None
    velocity: Optional[bool] = None
    time_avg_velocity: Optional[bool] = None
    window_avg_velocity: Optional[bool] = None
    velocity_magnitude: Optional[bool] = None
    time_avg_velocity_magnitude: Optional[bool] = None
    window_avg_velocity_magnitude: Optional[bool] = None
    wall_shear_stress: Optional[bool] = None          # surface probes only
    time_avg_wall_shear_stress: Optional[bool] = None  # surface probes only
    window_avg_wall_shear_stress: Optional[bool] = None  # surface probes only
    density: Optional[bool] = None
    time_avg_density: Optional[bool] = None
    window_avg_density: Optional[bool] = None
    pressure_std: Optional[bool] = None
    pressure_var: Optional[bool] = None


class ProbeFileInstance(BaseModel):
    """One <probe_file_instance> element inside <probe_file>."""
    name: str
    source_file: str                          # relative path to *.csv with probe locations
    probe_type: str = "volume"               # "volume" | "surface"
    radius: float = 0.0                       # m
    output_frequency: float = 1.0
    scientific_notation: bool = True
    output_precision: int = 7
    output_start_iteration: int = 0
    output_variables: ProbeOutputVariables = Field(default_factory=ProbeOutputVariables)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class Version(BaseModel):
    gui_version: str
    solver_version: str


# ---------------------------------------------------------------------------
# <simulation>
# ---------------------------------------------------------------------------

class SimulationGeneral(BaseModel):
    num_coarsest_iterations: int
    mach_factor: float = 1.0
    num_ramp_up_iterations: int = 200
    parameter_preset: Literal["default", "fan_noise"] = "default"


class Material(BaseModel):
    name: str
    density: float
    dynamic_viscosity: float
    temperature: float
    specific_gas_constant: float


class WallModeling(BaseModel):
    wall_model: Literal["GLW", "GWF", "WangMoin", "off"] = "GLW"
    coupling: Literal["adaptive_two-way", "two-way", "one-way", "off"] = "adaptive_two-way"
    transitional_bl_detection: Optional[bool] = None  # GHN only


class Simulation(BaseModel):
    general: SimulationGeneral
    material: Material
    wall_modeling: WallModeling


# ---------------------------------------------------------------------------
# <geometry>
# ---------------------------------------------------------------------------

class TriangleSplittingInstance(BaseModel):
    name: str
    active: bool = True
    max_absolute_edge_length: float = 0.0
    max_relative_edge_length: float = 9.0
    parts: List[str] = Field(default_factory=list)


class TriangleSplitting(BaseModel):
    active: bool
    max_absolute_edge_length: float
    max_relative_edge_length: float
    triangle_splitting_instances: List[TriangleSplittingInstance] = Field(default_factory=list)


class SurfaceMeshOptimization(BaseModel):
    triangle_splitting: TriangleSplitting


class DomainPartInstance(BaseModel):
    name: str
    location: str                   # "z_min" | "x_min" | "x_max" | "y_min" | "y_max" | "z_max"
    export_mesh: bool
    bounding_range: BoundingRange


class DomainPart(BaseModel):
    export_mesh: bool
    domain_part_instances: List[DomainPartInstance] = Field(default_factory=list)


class Geometry(BaseModel):
    # Exactly one of source_file / source_files is populated.
    # source_file:  single STL or ZIP filename  (1 geometry in assembly)
    # source_files: list of filenames           (multiple geometries in assembly)
    # Compute Engine sets the appropriate field; parser detects which tag is present.
    source_file: Optional[str] = None
    source_files: List[str] = Field(default_factory=list)
    baffle_parts: List[str] = Field(default_factory=list)
    domain_bounding_box: BoundingBox            # Computed
    triangle_plinth: bool = False
    surface_mesh_optimization: SurfaceMeshOptimization
    domain_part: DomainPart


# ---------------------------------------------------------------------------
# <meshing>
# ---------------------------------------------------------------------------

class MeshingGeneral(BaseModel):
    coarsest_mesh_size: float                   # Computed
    mesh_preview: bool
    mesh_export: bool
    refinement_level_transition_layers: int = 8


class BoxInstance(BaseModel):
    name: str
    refinement_level: int
    bounding_box: BoundingBox


class OffsetInstance(BaseModel):
    name: str
    normal_distance: float
    refinement_level: int
    parts: List[str] = Field(default_factory=list)


class CustomInstance(BaseModel):
    name: str
    refinement_level: int
    parts: List[str] = Field(default_factory=list)


class Refinement(BaseModel):
    box: List[BoxInstance] = Field(default_factory=list)
    offset: List[OffsetInstance] = Field(default_factory=list)
    custom: List[CustomInstance] = Field(default_factory=list)   # GHN only; empty for Aero


class RotatingInstance(BaseModel):
    """Overset rotating zone — Computed from STL wheel analysis."""
    name: str
    rpm: float
    center: XYZPos
    axis: XYZDir
    parts: List[str] = Field(default_factory=list)


class Overset(BaseModel):
    rotating: List[RotatingInstance] = Field(default_factory=list)   # Empty for GHN


class Meshing(BaseModel):
    general: MeshingGeneral
    refinement: Refinement
    overset: Overset


# ---------------------------------------------------------------------------
# <boundary_conditions>
# ---------------------------------------------------------------------------

class FluidBCVelocity(BaseModel):
    type: Literal["velocity"]
    velocity: XYZDir


class FluidBCNonReflectivePressure(BaseModel):
    type: Literal["non_reflective_pressure"]


class FluidBCStatic(BaseModel):
    type: Literal["static"]


class FluidBCSlip(BaseModel):
    type: Literal["slip"]


class FluidBCMoving(BaseModel):
    type: Literal["moving"]
    velocity: XYZDir


class FluidBCRotating(BaseModel):
    type: Literal["rotating"]
    rpm: float
    center: XYZPos
    axis: XYZDir


FluidBCSettings = Annotated[
    Union[
        FluidBCVelocity,
        FluidBCNonReflectivePressure,
        FluidBCStatic,
        FluidBCSlip,
        FluidBCMoving,
        FluidBCRotating,
    ],
    Field(discriminator="type"),
]


class InletInstance(BaseModel):
    name: str
    parts: List[str] = Field(default_factory=list)
    fluid_bc_settings: FluidBCVelocity


class OutletInstance(BaseModel):
    name: str
    parts: List[str] = Field(default_factory=list)
    fluid_bc_settings: FluidBCNonReflectivePressure


class WallInstance(BaseModel):
    name: str
    parts: List[str] = Field(default_factory=list)
    roughness: Optional[float] = None
    fluid_bc_settings: Annotated[
        Union[FluidBCStatic, FluidBCSlip, FluidBCMoving, FluidBCRotating],
        Field(discriminator="type"),
    ]


class BoundaryConditions(BaseModel):
    inlet: List[InletInstance] = Field(default_factory=list)
    outlet: List[OutletInstance] = Field(default_factory=list)
    wall: List[WallInstance] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# <sources>
# ---------------------------------------------------------------------------

class PorousAxis(BaseModel):
    x_dir: float
    y_dir: float
    z_dir: float


class PorousInstance(BaseModel):
    name: str
    inertial_resistance: float      # UserInput
    viscous_resistance: float       # UserInput
    porous_axis: PorousAxis         # Computed
    parts: List[str] = Field(default_factory=list)


class TurbulencePoint(BaseModel):
    """Only x_pos is present in turbulence point."""
    x_pos: float


class TurbulenceBoundingBox(BaseModel):
    """Turbulence generator bounding box — only y/z extents."""
    y_min: float
    z_min: float
    y_max: float
    z_max: float


class TurbulenceInstance(BaseModel):
    """Aero only — turbulence generator zones."""
    name: str
    num_eddies: int
    length_scale: float
    turbulence_intensity: float
    point: TurbulencePoint
    bounding_box: TurbulenceBoundingBox


class Sources(BaseModel):
    porous: List[PorousInstance] = Field(default_factory=list)
    turbulence: List[TurbulenceInstance] = Field(default_factory=list)   # Aero only


# ---------------------------------------------------------------------------
# <output>
# ---------------------------------------------------------------------------

class OutputVariablesFull(BaseModel):
    """Variables for full-volume output."""
    pressure: bool = False
    surface_normal: bool = False
    pressure_std: bool = False
    pressure_var: bool = False
    time_avg_pressure: bool = False
    time_avg_velocity: bool = False
    time_avg_wall_shear_stress: bool = False
    mesh_data: bool = False
    velocity: bool = False
    velocity_magnitude: bool = False
    wall_shear_stress: bool = False
    window_avg_pressure: bool = False
    window_avg_velocity: bool = False
    window_avg_wall_shear_stress: bool = False
    mesh_displacement: bool = False
    vorticity: bool = False
    vorticity_magnitude: bool = False
    lambda_1: bool = False
    lambda_2: bool = False
    lambda_3: bool = False
    q_criterion: bool = False
    temperature: bool = False
    time_avg_temperature: bool = False
    window_avg_temperature: bool = False


class OutputVariablesSurface(BaseModel):
    """Variables for surface output (subset of full)."""
    pressure: bool = False
    surface_normal: bool = False
    pressure_std: bool = False
    pressure_var: bool = False
    time_avg_pressure: bool = False
    time_avg_wall_shear_stress: bool = False
    velocity: bool = False
    velocity_magnitude: bool = False
    wall_shear_stress: bool = False
    window_avg_pressure: bool = False
    window_avg_wall_shear_stress: bool = False
    mesh_displacement: bool = False
    temperature: bool = False
    time_avg_temperature: bool = False
    window_avg_temperature: bool = False


class OutputGeneral(BaseModel):
    file_format: FileFormat
    output_coarsening: OutputCoarsening
    time_varying_geometry_output: bool
    merge_output_files: bool
    delete_unmerged_output_files: bool
    saved_states: int
    avg_start_coarsest_iteration: int
    avg_window_size: int
    output_frequency: int
    output_start_iteration: int
    output_variables_full: OutputVariablesFull
    output_variables_surface: OutputVariablesSurface
    bounding_box: BoundingBox


class MomentReferenceSystem(BaseModel):
    type: str = Field(alias="Type")             # XML tag is <Type> (capital T)
    origin: XYZPos
    roll_axis: XYZDir
    pitch_axis: XYZDir
    yaw_axis: XYZDir

    model_config = {"populate_by_name": True}


class ExportBounds(BaseModel):
    active: bool
    exclude_domain_parts: bool


class CoefficientsAlongAxis(BaseModel):
    num_sections_x: int
    num_sections_y: int
    num_sections_z: int
    export_bounds: ExportBounds


class AeroCoefficients(BaseModel):
    output_start_iteration: int
    coefficients_parts: bool
    reference_area_auto: bool
    reference_area: float
    reference_length_auto: bool
    reference_length: float
    coefficients_along_axis: CoefficientsAlongAxis
    passive_parts: List[str] = Field(default_factory=list)


class SectionCutOutputVariables(BaseModel):
    """Output variables specific to section cut (high-frequency transient)."""
    pressure: bool = False
    pressure_std: bool = False
    pressure_var: bool = False
    time_avg_pressure: bool = False
    window_avg_pressure: bool = False
    velocity: bool = False
    velocity_magnitude: bool = False
    time_avg_velocity: bool = False
    window_avg_velocity: bool = False
    mesh_displacement: bool = False
    vorticity: bool = False
    vorticity_magnitude: bool = False
    lambda_1: bool = False
    lambda_2: bool = False
    lambda_3: bool = False
    q_criterion: bool = False
    temperature: bool = False
    time_avg_temperature: bool = False
    window_avg_temperature: bool = False


class SectionCutInstance(BaseModel):
    """GHN only — high-frequency transient section cut output."""
    name: str
    merge_output_files: bool
    delete_unmerged_output_files: bool
    triangulation: bool
    file_format: FileFormat
    axis: XYZDir
    point: XYZPos
    bounding_box: BoundingBox
    output_frequency: float
    output_start_iteration: int
    output_variables: SectionCutOutputVariables


class PartialSurfaceOutputVariables(BaseModel):
    pressure: bool = False
    pressure_std: bool = False
    pressure_var: bool = False
    time_avg_pressure: bool = False
    window_avg_pressure: bool = False
    velocity: bool = False
    velocity_magnitude: bool = False
    wall_shear_stress: bool = False
    time_avg_wall_shear_stress: bool = False
    window_avg_wall_shear_stress: bool = False
    surface_normal: bool = False
    mesh_displacement: bool = False
    temperature: bool = False
    time_avg_temperature: bool = False
    window_avg_temperature: bool = False


class PartialSurfaceInstance(BaseModel):
    name: str
    parts: List[str] = Field(default_factory=list)
    merge_output_files: bool
    delete_unmerged_output_files: bool
    file_format: FileFormat
    output_frequency: float
    output_start_iteration: int
    output_variables: PartialSurfaceOutputVariables


class PartialVolumeOutputVariables(BaseModel):
    pressure: bool = False
    pressure_std: bool = False
    pressure_var: bool = False
    time_avg_pressure: bool = False
    window_avg_pressure: bool = False
    velocity: bool = False
    velocity_magnitude: bool = False
    time_avg_velocity: bool = False
    window_avg_velocity: bool = False
    mesh_displacement: bool = False
    vorticity: bool = False
    vorticity_magnitude: bool = False
    lambda_1: bool = False
    lambda_2: bool = False
    lambda_3: bool = False
    q_criterion: bool = False
    temperature: bool = False
    time_avg_temperature: bool = False
    window_avg_temperature: bool = False


class PartialVolumeInstance(BaseModel):
    name: str
    merge_output_files: bool
    delete_unmerged_output_files: bool
    file_format: FileFormat
    output_frequency: float
    output_start_iteration: int
    bounding_box: BoundingBox
    output_variables: PartialVolumeOutputVariables
    output_coarsening: Optional[OutputCoarsening] = None


class Output(BaseModel):
    general: OutputGeneral
    moment_reference_system: MomentReferenceSystem
    aero_coefficients: AeroCoefficients
    section_cut: List[SectionCutInstance] = Field(default_factory=list)     # GHN only
    probe_file: List[ProbeFileInstance] = Field(default_factory=list)
    partial_surface: List[PartialSurfaceInstance] = Field(default_factory=list)
    partial_volume: List[PartialVolumeInstance] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Root model
# ---------------------------------------------------------------------------

class UfxSolverDeck(BaseModel):
    version: Version
    simulation: Simulation
    geometry: Geometry
    meshing: Meshing
    boundary_conditions: BoundaryConditions
    sources: Sources
    output: Output
