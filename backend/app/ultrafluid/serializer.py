"""
Ultrafluid XML serializer: UfxSolverDeck Pydantic model → XML bytes.

Uses lxml.etree for robust XML generation.
"""

from __future__ import annotations

from lxml import etree

from .schema import (
    AeroCoefficients,
    BoundaryConditions,
    BoundingBox,
    BoundingRange,
    BoxInstance,
    CustomInstance,
    DomainPart,
    DomainPartInstance,
    FileFormat,
    FluidBCMoving,
    FluidBCNonReflectivePressure,
    FluidBCRotating,
    FluidBCSlip,
    FluidBCStatic,
    FluidBCVelocity,
    Geometry,
    InletInstance,
    Material,
    Meshing,
    MeshingGeneral,
    MomentReferenceSystem,
    OffsetInstance,
    Output,
    OutputCoarsening,
    OutputGeneral,
    OutputVariablesFull,
    OutputVariablesSurface,
    Overset,
    PartialSurfaceInstance,
    PartialSurfaceOutputVariables,
    PartialVolumeInstance,
    PartialVolumeOutputVariables,
    PorousAxis,
    PorousInstance,
    ProbeFileInstance,
    ProbeOutputVariables,
    Refinement,
    RotatingInstance,
    SectionCutInstance,
    SectionCutOutputVariables,
    Simulation,
    SimulationGeneral,
    Sources,
    SurfaceMeshOptimization,
    TurbulenceInstance,
    UfxSolverDeck,
    Version,
    WallInstance,
    WallModeling,
    XYZDir,
    XYZPos,
    OutletInstance,
)

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

_E = etree.SubElement


def _sub(parent: etree._Element, tag: str, text: str) -> etree._Element:
    el = etree.SubElement(parent, tag)
    el.text = text
    return el


def _sub_bool(parent: etree._Element, tag: str, value: bool) -> None:
    _sub(parent, tag, "true" if value else "false")


def _sub_float(parent: etree._Element, tag: str, value: float) -> None:
    _sub(parent, tag, str(value))


def _sub_int(parent: etree._Element, tag: str, value: int) -> None:
    _sub(parent, tag, str(value))


def _sub_str(parent: etree._Element, tag: str, value: str) -> None:
    _sub(parent, tag, value)


def _sub_names(parent: etree._Element, wrapper_tag: str, names: list[str]) -> etree._Element:
    """Write a list of strings as repeated <name> children under a wrapper element."""
    wrapper = etree.SubElement(parent, wrapper_tag)
    for name in names:
        _sub(wrapper, "name", name)
    return wrapper


# ---------------------------------------------------------------------------
# Common sub-serializers
# ---------------------------------------------------------------------------

def _ser_xyz_pos(parent: etree._Element, tag: str, pos: XYZPos) -> None:
    el = etree.SubElement(parent, tag)
    _sub_float(el, "x_pos", pos.x_pos)
    _sub_float(el, "y_pos", pos.y_pos)
    _sub_float(el, "z_pos", pos.z_pos)


def _ser_xyz_dir(parent: etree._Element, tag: str, d: XYZDir) -> None:
    el = etree.SubElement(parent, tag)
    _sub_float(el, "x_dir", d.x_dir)
    _sub_float(el, "y_dir", d.y_dir)
    _sub_float(el, "z_dir", d.z_dir)


def _ser_bounding_box(parent: etree._Element, tag: str, bb: BoundingBox) -> None:
    el = etree.SubElement(parent, tag)
    _sub_float(el, "x_min", bb.x_min)
    _sub_float(el, "x_max", bb.x_max)
    _sub_float(el, "y_min", bb.y_min)
    _sub_float(el, "y_max", bb.y_max)
    _sub_float(el, "z_min", bb.z_min)
    _sub_float(el, "z_max", bb.z_max)


def _ser_bounding_range(parent: etree._Element, tag: str, br: BoundingRange) -> None:
    el = etree.SubElement(parent, tag)
    _sub_float(el, "x_min", br.x_min)
    _sub_float(el, "x_max", br.x_max)
    _sub_float(el, "y_min", br.y_min)
    _sub_float(el, "y_max", br.y_max)


def _ser_file_format(parent: etree._Element, ff: FileFormat) -> None:
    el = etree.SubElement(parent, "file_format")
    _sub_bool(el, "ensight", ff.ensight)
    _sub_bool(el, "h3d", ff.h3d)


def _ser_output_coarsening(parent: etree._Element, oc: OutputCoarsening) -> None:
    el = etree.SubElement(parent, "output_coarsening")
    _sub_bool(el, "active", oc.active)
    _sub_int(el, "coarsen_by_num_refinement_levels", oc.coarsen_by_num_refinement_levels)
    _sub_int(el, "coarsest_target_refinement_level", oc.coarsest_target_refinement_level)
    _sub_bool(el, "export_uncoarsened_voxels", oc.export_uncoarsened_voxels)


# ---------------------------------------------------------------------------
# <version>
# ---------------------------------------------------------------------------

def _ser_version(parent: etree._Element, v: Version) -> None:
    el = etree.SubElement(parent, "version")
    _sub_str(el, "gui_version", v.gui_version)
    _sub_str(el, "solver_version", v.solver_version)


# ---------------------------------------------------------------------------
# <simulation>
# ---------------------------------------------------------------------------

def _ser_simulation(parent: etree._Element, s: Simulation) -> None:
    el = etree.SubElement(parent, "simulation")

    gen = etree.SubElement(el, "general")
    _sub_int(gen, "num_coarsest_iterations", s.general.num_coarsest_iterations)
    _sub_float(gen, "mach_factor", s.general.mach_factor)
    _sub_int(gen, "num_ramp_up_iterations", s.general.num_ramp_up_iterations)
    _sub_str(gen, "parameter_preset", s.general.parameter_preset)

    mat = etree.SubElement(el, "material")
    _sub_str(mat, "name", s.material.name)
    _sub_float(mat, "density", s.material.density)
    _sub_float(mat, "dynamic_viscosity", s.material.dynamic_viscosity)
    _sub_float(mat, "temperature", s.material.temperature)
    _sub_float(mat, "specific_gas_constant", s.material.specific_gas_constant)

    wm = etree.SubElement(el, "wall_modeling")
    _sub_str(wm, "wall_model", s.wall_modeling.wall_model)
    _sub_str(wm, "coupling", s.wall_modeling.coupling)
    if s.wall_modeling.transitional_bl_detection is not None:
        _sub_bool(wm, "transitional_bl_detection", s.wall_modeling.transitional_bl_detection)


# ---------------------------------------------------------------------------
# <geometry>
# ---------------------------------------------------------------------------

def _ser_geometry(parent: etree._Element, g: Geometry) -> None:
    el = etree.SubElement(parent, "geometry")

    if g.source_files:
        sfs_el = etree.SubElement(el, "source_files")
        for name in g.source_files:
            _sub_str(sfs_el, "name", name)
    elif g.source_file:
        _sub_str(el, "source_file", g.source_file)

    baffle = etree.SubElement(el, "baffle_parts")
    for name in g.baffle_parts:
        _sub_str(baffle, "name", name)

    _ser_bounding_box(el, "domain_bounding_box", g.domain_bounding_box)
    _sub_bool(el, "triangle_plinth", g.triangle_plinth)

    smo = etree.SubElement(el, "surface_mesh_optimization")
    ts_el = etree.SubElement(smo, "triangle_splitting")
    _sub_bool(ts_el, "active", g.surface_mesh_optimization.triangle_splitting.active)
    _sub_float(ts_el, "max_absolute_edge_length",
               g.surface_mesh_optimization.triangle_splitting.max_absolute_edge_length)
    _sub_float(ts_el, "max_relative_edge_length",
               g.surface_mesh_optimization.triangle_splitting.max_relative_edge_length)

    dp_el = etree.SubElement(el, "domain_part")
    _sub_bool(dp_el, "export_mesh", g.domain_part.export_mesh)
    for inst in g.domain_part.domain_part_instances:
        inst_el = etree.SubElement(dp_el, "domain_part_instance")
        _sub_str(inst_el, "name", inst.name)
        _sub_str(inst_el, "location", inst.location)
        _sub_bool(inst_el, "export_mesh", inst.export_mesh)
        _ser_bounding_range(inst_el, "bounding_range", inst.bounding_range)


# ---------------------------------------------------------------------------
# <meshing>
# ---------------------------------------------------------------------------

def _ser_meshing(parent: etree._Element, m: Meshing) -> None:
    el = etree.SubElement(parent, "meshing")

    gen = etree.SubElement(el, "general")
    _sub_float(gen, "coarsest_mesh_size", m.general.coarsest_mesh_size)
    _sub_bool(gen, "mesh_preview", m.general.mesh_preview)
    _sub_bool(gen, "mesh_export", m.general.mesh_export)
    _sub_int(gen, "refinement_level_transition_layers",
             m.general.refinement_level_transition_layers)

    ref = etree.SubElement(el, "refinement")

    if m.refinement.box:
        box_wrapper = etree.SubElement(ref, "box")
        for inst in m.refinement.box:
            inst_el = etree.SubElement(box_wrapper, "box_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_int(inst_el, "refinement_level", inst.refinement_level)
            _ser_bounding_box(inst_el, "bounding_box", inst.bounding_box)
    else:
        etree.SubElement(ref, "box")

    if m.refinement.offset:
        off_wrapper = etree.SubElement(ref, "offset")
        for inst in m.refinement.offset:
            inst_el = etree.SubElement(off_wrapper, "offset_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_float(inst_el, "normal_distance", inst.normal_distance)
            _sub_int(inst_el, "refinement_level", inst.refinement_level)
            if inst.parts:
                parts_el = etree.SubElement(inst_el, "parts")
                for p in inst.parts:
                    _sub_str(parts_el, "name", p)
    else:
        etree.SubElement(ref, "offset")

    if m.refinement.custom:
        cust_wrapper = etree.SubElement(ref, "custom")
        for inst in m.refinement.custom:
            inst_el = etree.SubElement(cust_wrapper, "custom_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_int(inst_el, "refinement_level", inst.refinement_level)
            if inst.parts:
                parts_el = etree.SubElement(inst_el, "parts")
                for p in inst.parts:
                    _sub_str(parts_el, "name", p)
    else:
        etree.SubElement(ref, "custom")

    overset_el = etree.SubElement(el, "overset")
    if m.overset.rotating:
        rot_wrapper = etree.SubElement(overset_el, "rotating")
        for inst in m.overset.rotating:
            inst_el = etree.SubElement(rot_wrapper, "rotating_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_float(inst_el, "rpm", inst.rpm)
            _ser_xyz_pos(inst_el, "center", inst.center)
            _ser_xyz_dir(inst_el, "axis", inst.axis)
            if inst.parts:
                parts_el = etree.SubElement(inst_el, "parts")
                for p in inst.parts:
                    _sub_str(parts_el, "name", p)


# ---------------------------------------------------------------------------
# <boundary_conditions>
# ---------------------------------------------------------------------------

def _ser_fluid_bc(parent: etree._Element, bc) -> None:
    el = etree.SubElement(parent, "fluid_bc_settings")
    if isinstance(bc, FluidBCVelocity):
        _ser_xyz_dir(el, "velocity", bc.velocity)
        _sub_str(el, "type", bc.type)
    elif isinstance(bc, FluidBCNonReflectivePressure):
        _sub_str(el, "type", bc.type)
    elif isinstance(bc, FluidBCStatic):
        _sub_str(el, "type", bc.type)
    elif isinstance(bc, FluidBCSlip):
        _sub_str(el, "type", bc.type)
    elif isinstance(bc, FluidBCMoving):
        _ser_xyz_dir(el, "velocity", bc.velocity)
        _sub_str(el, "type", bc.type)
    elif isinstance(bc, FluidBCRotating):
        _sub_float(el, "rpm", bc.rpm)
        _sub_str(el, "type", bc.type)
        _ser_xyz_pos(el, "center", bc.center)
        _ser_xyz_dir(el, "axis", bc.axis)


def _ser_boundary_conditions(parent: etree._Element, bc: BoundaryConditions) -> None:
    el = etree.SubElement(parent, "boundary_conditions")

    inlet_el = etree.SubElement(el, "inlet")
    for inst in bc.inlet:
        inst_el = etree.SubElement(inlet_el, "inlet_instance")
        _sub_str(inst_el, "name", inst.name)
        parts_el = etree.SubElement(inst_el, "parts")
        for p in inst.parts:
            _sub_str(parts_el, "name", p)
        _ser_fluid_bc(inst_el, inst.fluid_bc_settings)

    outlet_el = etree.SubElement(el, "outlet")
    for inst in bc.outlet:
        inst_el = etree.SubElement(outlet_el, "outlet_instance")
        _sub_str(inst_el, "name", inst.name)
        parts_el = etree.SubElement(inst_el, "parts")
        for p in inst.parts:
            _sub_str(parts_el, "name", p)
        _ser_fluid_bc(inst_el, inst.fluid_bc_settings)

    etree.SubElement(el, "static")

    if bc.wall:
        wall_el = etree.SubElement(el, "wall")
        for inst in bc.wall:
            inst_el = etree.SubElement(wall_el, "wall_instance")
            _sub_str(inst_el, "name", inst.name)
            parts_el = etree.SubElement(inst_el, "parts")
            for p in inst.parts:
                _sub_str(parts_el, "name", p)
            if inst.roughness is not None:
                _sub_float(inst_el, "roughness", inst.roughness)
            _ser_fluid_bc(inst_el, inst.fluid_bc_settings)
    else:
        etree.SubElement(el, "wall")


# ---------------------------------------------------------------------------
# <sources>
# ---------------------------------------------------------------------------

def _ser_sources(parent: etree._Element, s: Sources) -> None:
    el = etree.SubElement(parent, "sources")

    if s.porous:
        porous_el = etree.SubElement(el, "porous")
        for inst in s.porous:
            inst_el = etree.SubElement(porous_el, "porous_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_float(inst_el, "inertial_resistance", inst.inertial_resistance)
            _sub_float(inst_el, "viscous_resistance", inst.viscous_resistance)
            axis_el = etree.SubElement(inst_el, "porous_axis")
            _sub_float(axis_el, "x_dir", inst.porous_axis.x_dir)
            _sub_float(axis_el, "y_dir", inst.porous_axis.y_dir)
            _sub_float(axis_el, "z_dir", inst.porous_axis.z_dir)
            parts_el = etree.SubElement(inst_el, "parts")
            for p in inst.parts:
                _sub_str(parts_el, "name", p)
    else:
        etree.SubElement(el, "porous")

    etree.SubElement(el, "mrf")

    if s.turbulence:
        turb_el = etree.SubElement(el, "turbulence")
        for inst in s.turbulence:
            inst_el = etree.SubElement(turb_el, "turbulence_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_int(inst_el, "num_eddies", inst.num_eddies)
            _sub_float(inst_el, "length_scale", inst.length_scale)
            _sub_float(inst_el, "turbulence_intensity", inst.turbulence_intensity)
            pt_el = etree.SubElement(inst_el, "point")
            _sub_float(pt_el, "x_pos", inst.point.x_pos)
            bb_el = etree.SubElement(inst_el, "bounding_box")
            _sub_float(bb_el, "y_min", inst.bounding_box.y_min)
            _sub_float(bb_el, "z_min", inst.bounding_box.z_min)
            _sub_float(bb_el, "y_max", inst.bounding_box.y_max)
            _sub_float(bb_el, "z_max", inst.bounding_box.z_max)


# ---------------------------------------------------------------------------
# <output>
# ---------------------------------------------------------------------------

def _ser_output_variables_full(parent: etree._Element, v: OutputVariablesFull) -> None:
    el = etree.SubElement(parent, "output_variables_full")
    _sub_bool(el, "pressure", v.pressure)
    _sub_bool(el, "surface_normal", v.surface_normal)
    _sub_bool(el, "pressure_std", v.pressure_std)
    _sub_bool(el, "pressure_var", v.pressure_var)
    _sub_bool(el, "time_avg_pressure", v.time_avg_pressure)
    _sub_bool(el, "time_avg_velocity", v.time_avg_velocity)
    _sub_bool(el, "time_avg_wall_shear_stress", v.time_avg_wall_shear_stress)
    _sub_bool(el, "mesh_data", v.mesh_data)
    _sub_bool(el, "velocity", v.velocity)
    _sub_bool(el, "velocity_magnitude", v.velocity_magnitude)
    _sub_bool(el, "wall_shear_stress", v.wall_shear_stress)
    _sub_bool(el, "window_avg_pressure", v.window_avg_pressure)
    _sub_bool(el, "window_avg_velocity", v.window_avg_velocity)
    _sub_bool(el, "window_avg_wall_shear_stress", v.window_avg_wall_shear_stress)
    _sub_bool(el, "mesh_displacement", v.mesh_displacement)
    _sub_bool(el, "vorticity", v.vorticity)
    _sub_bool(el, "vorticity_magnitude", v.vorticity_magnitude)
    _sub_bool(el, "lambda_1", v.lambda_1)
    _sub_bool(el, "lambda_2", v.lambda_2)
    _sub_bool(el, "lambda_3", v.lambda_3)
    _sub_bool(el, "q_criterion", v.q_criterion)
    _sub_bool(el, "temperature", v.temperature)
    _sub_bool(el, "time_avg_temperature", v.time_avg_temperature)
    _sub_bool(el, "window_avg_temperature", v.window_avg_temperature)


def _ser_output_variables_surface(parent: etree._Element, v: OutputVariablesSurface) -> None:
    el = etree.SubElement(parent, "output_variables_surface")
    _sub_bool(el, "pressure", v.pressure)
    _sub_bool(el, "surface_normal", v.surface_normal)
    _sub_bool(el, "pressure_std", v.pressure_std)
    _sub_bool(el, "pressure_var", v.pressure_var)
    _sub_bool(el, "time_avg_pressure", v.time_avg_pressure)
    _sub_bool(el, "time_avg_wall_shear_stress", v.time_avg_wall_shear_stress)
    _sub_bool(el, "velocity", v.velocity)
    _sub_bool(el, "velocity_magnitude", v.velocity_magnitude)
    _sub_bool(el, "wall_shear_stress", v.wall_shear_stress)
    _sub_bool(el, "window_avg_pressure", v.window_avg_pressure)
    _sub_bool(el, "window_avg_wall_shear_stress", v.window_avg_wall_shear_stress)
    _sub_bool(el, "mesh_displacement", v.mesh_displacement)
    _sub_bool(el, "temperature", v.temperature)
    _sub_bool(el, "time_avg_temperature", v.time_avg_temperature)
    _sub_bool(el, "window_avg_temperature", v.window_avg_temperature)


def _ser_section_cut_output_variables(parent: etree._Element, v: SectionCutOutputVariables) -> None:
    el = etree.SubElement(parent, "output_variables")
    _sub_bool(el, "pressure", v.pressure)
    _sub_bool(el, "pressure_std", v.pressure_std)
    _sub_bool(el, "pressure_var", v.pressure_var)
    _sub_bool(el, "time_avg_pressure", v.time_avg_pressure)
    _sub_bool(el, "window_avg_pressure", v.window_avg_pressure)
    _sub_bool(el, "velocity", v.velocity)
    _sub_bool(el, "velocity_magnitude", v.velocity_magnitude)
    _sub_bool(el, "time_avg_velocity", v.time_avg_velocity)
    _sub_bool(el, "window_avg_velocity", v.window_avg_velocity)
    _sub_bool(el, "mesh_displacement", v.mesh_displacement)
    _sub_bool(el, "vorticity", v.vorticity)
    _sub_bool(el, "vorticity_magnitude", v.vorticity_magnitude)
    _sub_bool(el, "lambda_1", v.lambda_1)
    _sub_bool(el, "lambda_2", v.lambda_2)
    _sub_bool(el, "lambda_3", v.lambda_3)
    _sub_bool(el, "q_criterion", v.q_criterion)
    _sub_bool(el, "temperature", v.temperature)
    _sub_bool(el, "time_avg_temperature", v.time_avg_temperature)
    _sub_bool(el, "window_avg_temperature", v.window_avg_temperature)


def _ser_partial_surface_output_variables(parent: etree._Element, v: PartialSurfaceOutputVariables) -> None:
    el = etree.SubElement(parent, "output_variables")
    _sub_bool(el, "pressure", v.pressure)
    _sub_bool(el, "pressure_std", v.pressure_std)
    _sub_bool(el, "pressure_var", v.pressure_var)
    _sub_bool(el, "time_avg_pressure", v.time_avg_pressure)
    _sub_bool(el, "window_avg_pressure", v.window_avg_pressure)
    _sub_bool(el, "velocity", v.velocity)
    _sub_bool(el, "velocity_magnitude", v.velocity_magnitude)
    _sub_bool(el, "wall_shear_stress", v.wall_shear_stress)
    _sub_bool(el, "time_avg_wall_shear_stress", v.time_avg_wall_shear_stress)
    _sub_bool(el, "window_avg_wall_shear_stress", v.window_avg_wall_shear_stress)
    _sub_bool(el, "surface_normal", v.surface_normal)
    _sub_bool(el, "mesh_displacement", v.mesh_displacement)
    _sub_bool(el, "temperature", v.temperature)
    _sub_bool(el, "time_avg_temperature", v.time_avg_temperature)
    _sub_bool(el, "window_avg_temperature", v.window_avg_temperature)


def _ser_partial_volume_output_variables(parent: etree._Element, v: PartialVolumeOutputVariables) -> None:
    el = etree.SubElement(parent, "output_variables")
    _sub_bool(el, "pressure", v.pressure)
    _sub_bool(el, "pressure_std", v.pressure_std)
    _sub_bool(el, "pressure_var", v.pressure_var)
    _sub_bool(el, "time_avg_pressure", v.time_avg_pressure)
    _sub_bool(el, "window_avg_pressure", v.window_avg_pressure)
    _sub_bool(el, "velocity", v.velocity)
    _sub_bool(el, "velocity_magnitude", v.velocity_magnitude)
    _sub_bool(el, "time_avg_velocity", v.time_avg_velocity)
    _sub_bool(el, "window_avg_velocity", v.window_avg_velocity)
    _sub_bool(el, "mesh_displacement", v.mesh_displacement)
    _sub_bool(el, "vorticity", v.vorticity)
    _sub_bool(el, "vorticity_magnitude", v.vorticity_magnitude)
    _sub_bool(el, "lambda_1", v.lambda_1)
    _sub_bool(el, "lambda_2", v.lambda_2)
    _sub_bool(el, "lambda_3", v.lambda_3)
    _sub_bool(el, "q_criterion", v.q_criterion)
    _sub_bool(el, "temperature", v.temperature)
    _sub_bool(el, "time_avg_temperature", v.time_avg_temperature)
    _sub_bool(el, "window_avg_temperature", v.window_avg_temperature)


def _ser_probe_output_variables(parent: etree._Element, v: ProbeOutputVariables) -> None:
    el = etree.SubElement(parent, "output_variables")
    # Only emit explicitly set variables (None = omit, use solver default)
    for field_name in [
        "pressure", "time_avg_pressure", "window_avg_pressure", "cp",
        "velocity", "time_avg_velocity", "window_avg_velocity",
        "velocity_magnitude", "time_avg_velocity_magnitude", "window_avg_velocity_magnitude",
        "wall_shear_stress", "time_avg_wall_shear_stress", "window_avg_wall_shear_stress",
        "density", "time_avg_density", "window_avg_density",
        "pressure_std", "pressure_var",
    ]:
        val = getattr(v, field_name)
        if val is not None:
            _sub_bool(el, field_name, val)


def _ser_output(parent: etree._Element, o: Output) -> None:
    el = etree.SubElement(parent, "output")

    gen = etree.SubElement(el, "general")
    _ser_file_format(gen, o.general.file_format)
    _ser_output_coarsening(gen, o.general.output_coarsening)
    _sub_bool(gen, "time_varying_geometry_output", o.general.time_varying_geometry_output)
    _sub_bool(gen, "merge_output_files", o.general.merge_output_files)
    _sub_bool(gen, "delete_unmerged_output_files", o.general.delete_unmerged_output_files)
    _sub_int(gen, "saved_states", o.general.saved_states)
    _sub_int(gen, "avg_start_coarsest_iteration", o.general.avg_start_coarsest_iteration)
    _sub_int(gen, "avg_window_size", o.general.avg_window_size)
    _sub_int(gen, "output_frequency", o.general.output_frequency)
    _sub_int(gen, "output_start_iteration", o.general.output_start_iteration)
    _ser_output_variables_full(gen, o.general.output_variables_full)
    _ser_output_variables_surface(gen, o.general.output_variables_surface)
    _ser_bounding_box(gen, "bounding_box", o.general.bounding_box)

    mrs = etree.SubElement(el, "moment_reference_system")
    _sub_str(mrs, "Type", o.moment_reference_system.type)
    _ser_xyz_pos(mrs, "origin", o.moment_reference_system.origin)
    _ser_xyz_dir(mrs, "roll_axis", o.moment_reference_system.roll_axis)
    _ser_xyz_dir(mrs, "pitch_axis", o.moment_reference_system.pitch_axis)
    _ser_xyz_dir(mrs, "yaw_axis", o.moment_reference_system.yaw_axis)

    ac = etree.SubElement(el, "aero_coefficients")
    _sub_int(ac, "output_start_iteration", o.aero_coefficients.output_start_iteration)
    _sub_bool(ac, "coefficients_parts", o.aero_coefficients.coefficients_parts)
    _sub_bool(ac, "reference_area_auto", o.aero_coefficients.reference_area_auto)
    _sub_float(ac, "reference_area", o.aero_coefficients.reference_area)
    _sub_bool(ac, "reference_length_auto", o.aero_coefficients.reference_length_auto)
    _sub_float(ac, "reference_length", o.aero_coefficients.reference_length)
    caa = etree.SubElement(ac, "coefficients_along_axis")
    _sub_int(caa, "num_sections_x", o.aero_coefficients.coefficients_along_axis.num_sections_x)
    _sub_int(caa, "num_sections_y", o.aero_coefficients.coefficients_along_axis.num_sections_y)
    _sub_int(caa, "num_sections_z", o.aero_coefficients.coefficients_along_axis.num_sections_z)
    eb = etree.SubElement(caa, "export_bounds")
    _sub_bool(eb, "active", o.aero_coefficients.coefficients_along_axis.export_bounds.active)
    _sub_bool(eb, "exclude_domain_parts",
              o.aero_coefficients.coefficients_along_axis.export_bounds.exclude_domain_parts)
    passive_el = etree.SubElement(ac, "passive_parts")
    for p in o.aero_coefficients.passive_parts:
        _sub_str(passive_el, "name", p)

    if o.section_cut:
        sc_wrapper = etree.SubElement(el, "section_cut")
        for inst in o.section_cut:
            inst_el = etree.SubElement(sc_wrapper, "section_cut_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_bool(inst_el, "merge_output_files", inst.merge_output_files)
            _sub_bool(inst_el, "delete_unmerged_output_files", inst.delete_unmerged_output_files)
            _sub_bool(inst_el, "triangulation", inst.triangulation)
            _ser_file_format(inst_el, inst.file_format)
            _ser_xyz_dir(inst_el, "axis", inst.axis)
            _ser_xyz_pos(inst_el, "point", inst.point)
            _ser_bounding_box(inst_el, "bounding_box", inst.bounding_box)
            _sub_float(inst_el, "output_frequency", inst.output_frequency)
            _sub_int(inst_el, "output_start_iteration", inst.output_start_iteration)
            _ser_section_cut_output_variables(inst_el, inst.output_variables)
    else:
        etree.SubElement(el, "section_cut")

    if o.probe_file:
        pf_wrapper = etree.SubElement(el, "probe_file")
        for inst in o.probe_file:
            inst_el = etree.SubElement(pf_wrapper, "probe_file_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_str(inst_el, "source_file", inst.source_file)
            _sub_str(inst_el, "type", inst.probe_type)
            _sub_float(inst_el, "radius", inst.radius)
            _sub_float(inst_el, "output_frequency", inst.output_frequency)
            _sub_bool(inst_el, "scientific_notation", inst.scientific_notation)
            _sub_int(inst_el, "output_precision", inst.output_precision)
            _sub_int(inst_el, "output_start_iteration", inst.output_start_iteration)
            _ser_probe_output_variables(inst_el, inst.output_variables)
    else:
        etree.SubElement(el, "probe_file")

    if o.partial_surface:
        ps_wrapper = etree.SubElement(el, "partial_surface")
        for inst in o.partial_surface:
            inst_el = etree.SubElement(ps_wrapper, "partial_surface_instance")
            _sub_str(inst_el, "name", inst.name)
            parts_el = etree.SubElement(inst_el, "parts")
            for p in inst.parts:
                _sub_str(parts_el, "name", p)
            _sub_bool(inst_el, "merge_output_files", inst.merge_output_files)
            _sub_bool(inst_el, "delete_unmerged_output_files", inst.delete_unmerged_output_files)
            _ser_file_format(inst_el, inst.file_format)
            _sub_float(inst_el, "output_frequency", inst.output_frequency)
            _sub_int(inst_el, "output_start_iteration", inst.output_start_iteration)
            _ser_partial_surface_output_variables(inst_el, inst.output_variables)
    else:
        etree.SubElement(el, "partial_surface")

    if o.partial_volume:
        pv_wrapper = etree.SubElement(el, "partial_volume")
        for inst in o.partial_volume:
            inst_el = etree.SubElement(pv_wrapper, "partial_volume_instance")
            _sub_str(inst_el, "name", inst.name)
            _sub_bool(inst_el, "merge_output_files", inst.merge_output_files)
            _sub_bool(inst_el, "delete_unmerged_output_files", inst.delete_unmerged_output_files)
            _ser_file_format(inst_el, inst.file_format)
            _sub_float(inst_el, "output_frequency", inst.output_frequency)
            _sub_int(inst_el, "output_start_iteration", inst.output_start_iteration)
            _ser_bounding_box(inst_el, "bounding_box", inst.bounding_box)
            _ser_partial_volume_output_variables(inst_el, inst.output_variables)
            if inst.output_coarsening is not None:
                _ser_output_coarsening(inst_el, inst.output_coarsening)
    else:
        etree.SubElement(el, "partial_volume")

    etree.SubElement(el, "monitoring_surface")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize_ufx(deck: UfxSolverDeck, *, pretty_print: bool = True) -> bytes:
    """Serialize a UfxSolverDeck model to Ultrafluid XML bytes.

    Args:
        deck: The solver deck model to serialize.
        pretty_print: If True, output is indented for readability.

    Returns:
        XML content as UTF-8 bytes (includes XML declaration).
    """
    root = etree.Element("uFX_solver_deck")

    _ser_version(root, deck.version)
    _ser_simulation(root, deck.simulation)
    _ser_geometry(root, deck.geometry)
    _ser_meshing(root, deck.meshing)
    _ser_boundary_conditions(root, deck.boundary_conditions)
    _ser_sources(root, deck.sources)
    _ser_output(root, deck.output)

    return etree.tostring(
        root,
        pretty_print=pretty_print,
        xml_declaration=True,
        encoding="UTF-8",
    )
