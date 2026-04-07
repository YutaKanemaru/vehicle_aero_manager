"""
Pydantic schema for Template settings JSON.

The settings field stored in TemplateVersion follows a 4-section structure:
  - setup_option:         boolean flags controlling computation behaviour
  - simulation_parameter: fixed physical values
  - setup:                geometry-relative sizing rules for mesh / BCs
  - target_names:         part-name matching patterns
"""

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# setup_option
# ---------------------------------------------------------------------------

class SimulationOption(BaseModel):
    temperature_degree: bool = True          # input temperature is °C (converted to K)
    simulation_time_with_FP: bool = False    # use flow-passage time instead of fixed time


class MeshingOption(BaseModel):
    triangle_splitting: bool = True
    domain_bounding_box_relative: bool = True  # bbox defined relative to car dimensions
    box_offset_relative: bool = True
    box_refinement_porous: bool = True


class GroundOption(BaseModel):
    moving_ground: bool = True
    no_slip_static_ground_patch: bool = True
    ground_zmin_auto: bool = True
    boundary_layer_suction_position_from_belt_xmin: bool = True


class BeltOption(BaseModel):
    opt_belt_system: bool = True
    num_belts: int = 5
    include_wheel_belt_forces: bool = True
    wheel_belt_location_auto: bool = True


class TurbulenceGeneratorOption(BaseModel):
    activate_body_tg: bool = True
    activate_ground_tg: bool = True


class BoundaryConditionOption(BaseModel):
    ground: GroundOption = Field(default_factory=GroundOption)
    belt: BeltOption = Field(default_factory=BeltOption)
    turbulence_generator: TurbulenceGeneratorOption = Field(
        default_factory=TurbulenceGeneratorOption
    )


class SetupOption(BaseModel):
    simulation: SimulationOption = Field(default_factory=SimulationOption)
    meshing: MeshingOption = Field(default_factory=MeshingOption)
    boundary_condition: BoundaryConditionOption = Field(
        default_factory=BoundaryConditionOption
    )


# ---------------------------------------------------------------------------
# simulation_parameter
# ---------------------------------------------------------------------------

class SimulationParameter(BaseModel):
    inflow_velocity: float = 38.88          # m/s
    density: float = 1.2041                 # kg/m³
    dynamic_viscosity: float = 1.8194e-5   # kg/(s·m)
    temperature: float = 20.0              # °C (converted to K if temperature_degree=True)
    specific_gas_constant: float = 287.05  # J/(kg·K)
    mach_factor: float = 2.0
    num_ramp_up_iter: int = 200
    finest_resolution_size: float = 0.0015  # m
    number_of_resolution: int = 7           # coarsest = finest × 2^N
    simulation_time: float = 2.0            # seconds
    simulation_time_FP: float = 30.0        # flow passages


# ---------------------------------------------------------------------------
# setup — meshing
# ---------------------------------------------------------------------------

class BoxRefinement(BaseModel):
    level: int
    box: list[float] = Field(..., min_length=6, max_length=6)  # xmin,xmax,ymin,ymax,zmin,zmax


class OffsetRefinement(BaseModel):
    level: int
    normal_distance: float
    parts: list[str] = Field(default_factory=list)


class CustomRefinement(BaseModel):
    level: int
    parts: list[str]


class BeltSize(BaseModel):
    x: float
    y: float


class BoundaryConditionInput(BaseModel):
    belts: dict[str, Any] = Field(default_factory=dict)
    boundary_layer_suction_xpos: float = -1.1


class MeshingSetup(BaseModel):
    box_refinement: dict[str, BoxRefinement] = Field(default_factory=dict)
    part_box_refinement: dict[str, BoxRefinement] = Field(default_factory=dict)
    offset_refinement: dict[str, OffsetRefinement] = Field(default_factory=dict)
    custom_refinement: dict[str, CustomRefinement] = Field(default_factory=dict)


class Setup(BaseModel):
    # 6-element list: [x_min_mult, x_max_mult, y_min_mult, y_max_mult, z_min_mult, z_max_mult]
    domain_bounding_box: list[float] = Field(
        default=[-5.0, 15.0, -12.0, 12.0, 0.0, 20.0],
        min_length=6,
        max_length=6,
    )
    meshing: MeshingSetup = Field(default_factory=MeshingSetup)
    boundary_condition_input: BoundaryConditionInput = Field(
        default_factory=BoundaryConditionInput
    )


# ---------------------------------------------------------------------------
# target_names
# ---------------------------------------------------------------------------

class TargetNames(BaseModel):
    wheel: list[str] = Field(default_factory=list)
    rim: list[str] = Field(default_factory=list)
    porous: list[str] = Field(default_factory=list)
    car_bounding_box: list[str] = Field(default_factory=list)
    baffle: list[str] = Field(default_factory=list)
    triangle_splitting: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Root settings schema
# ---------------------------------------------------------------------------

class TemplateSettings(BaseModel):
    setup_option: SetupOption = Field(default_factory=SetupOption)
    simulation_parameter: SimulationParameter = Field(default_factory=SimulationParameter)
    setup: Setup = Field(default_factory=Setup)
    target_names: TargetNames = Field(default_factory=TargetNames)
