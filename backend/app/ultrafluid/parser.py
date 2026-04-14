"""
Ultrafluid XML parser: XML file → UfxSolverDeck Pydantic model.

Uses lxml.etree for robust XML parsing.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Union

from lxml import etree

from .schema import (
    AeroCoefficients,
    BoundaryConditions,
    BoundingBox,
    BoundingRange,
    BoxInstance,
    CoefficientsAlongAxis,
    CustomInstance,
    DomainPart,
    DomainPartInstance,
    ExportBounds,
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
    Refinement,
    RotatingInstance,
    SectionCutInstance,
    SectionCutOutputVariables,
    Simulation,
    SimulationGeneral,
    Sources,
    SurfaceMeshOptimization,
    TriangleSplitting,
    TriangleSplittingInstance,
    TurbulenceBoundingBox,
    TurbulenceInstance,
    TurbulencePoint,
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

def _find(el: etree._Element, tag: str) -> Optional[etree._Element]:
    return el.find(tag)


def _text(el: etree._Element, tag: str) -> str:
    child = el.find(tag)
    if child is None or child.text is None:
        raise ValueError(f"Missing element <{tag}> in <{el.tag}>")
    return child.text.strip()


def _text_opt(el: etree._Element, tag: str) -> Optional[str]:
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _bool(el: etree._Element, tag: str) -> bool:
    val = _text(el, tag).lower()
    if val == "true":
        return True
    if val == "false":
        return False
    raise ValueError(f"<{tag}> has non-boolean value: {val!r}")


def _bool_opt(el: etree._Element, tag: str) -> Optional[bool]:
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    val = child.text.strip().lower()
    if val == "true":
        return True
    if val == "false":
        return False
    raise ValueError(f"<{tag}> has non-boolean value: {val!r}")


def _float(el: etree._Element, tag: str) -> float:
    return float(_text(el, tag))


def _int(el: etree._Element, tag: str) -> int:
    return int(_text(el, tag))


def _names(el: etree._Element) -> List[str]:
    """Collect text of all <name> children."""
    return [n.text.strip() for n in el.findall("name") if n.text]


# ---------------------------------------------------------------------------
# Common sub-parsers
# ---------------------------------------------------------------------------

def _parse_xyz_pos(el: etree._Element) -> XYZPos:
    return XYZPos(
        x_pos=_float(el, "x_pos"),
        y_pos=_float(el, "y_pos"),
        z_pos=_float(el, "z_pos"),
    )


def _parse_xyz_dir(el: etree._Element) -> XYZDir:
    return XYZDir(
        x_dir=_float(el, "x_dir"),
        y_dir=_float(el, "y_dir"),
        z_dir=_float(el, "z_dir"),
    )


def _parse_bounding_box(el: etree._Element) -> BoundingBox:
    return BoundingBox(
        x_min=_float(el, "x_min"),
        x_max=_float(el, "x_max"),
        y_min=_float(el, "y_min"),
        y_max=_float(el, "y_max"),
        z_min=_float(el, "z_min"),
        z_max=_float(el, "z_max"),
    )


def _parse_bounding_range(el: etree._Element) -> BoundingRange:
    return BoundingRange(
        x_min=_float(el, "x_min"),
        x_max=_float(el, "x_max"),
        y_min=_float(el, "y_min"),
        y_max=_float(el, "y_max"),
    )


def _parse_file_format(el: etree._Element) -> FileFormat:
    return FileFormat(
        ensight=_bool(el, "ensight"),
        h3d=_bool(el, "h3d"),
    )


def _parse_output_coarsening(el: etree._Element) -> OutputCoarsening:
    return OutputCoarsening(
        active=_bool(el, "active"),
        coarsen_by_num_refinement_levels=_int(el, "coarsen_by_num_refinement_levels"),
        coarsest_target_refinement_level=_int(el, "coarsest_target_refinement_level"),
        export_uncoarsened_voxels=_bool(el, "export_uncoarsened_voxels"),
    )


# ---------------------------------------------------------------------------
# <version>
# ---------------------------------------------------------------------------

def _parse_version(el: etree._Element) -> Version:
    return Version(
        gui_version=_text(el, "gui_version"),
        solver_version=_text(el, "solver_version"),
    )


# ---------------------------------------------------------------------------
# <simulation>
# ---------------------------------------------------------------------------

def _parse_simulation(el: etree._Element) -> Simulation:
    gen_el = el.find("general")
    mat_el = el.find("material")
    wm_el = el.find("wall_modeling")

    general = SimulationGeneral(
        num_coarsest_iterations=_int(gen_el, "num_coarsest_iterations"),
        mach_factor=_float(gen_el, "mach_factor"),
        num_ramp_up_iterations=_int(gen_el, "num_ramp_up_iterations"),
        parameter_preset=_text(gen_el, "parameter_preset"),
    )

    material = Material(
        name=_text(mat_el, "name"),
        density=_float(mat_el, "density"),
        dynamic_viscosity=_float(mat_el, "dynamic_viscosity"),
        temperature=_float(mat_el, "temperature"),
        specific_gas_constant=_float(mat_el, "specific_gas_constant"),
    )

    wall_modeling = WallModeling(
        wall_model=_text(wm_el, "wall_model"),
        coupling=_text(wm_el, "coupling"),
        transitional_bl_detection=_bool_opt(wm_el, "transitional_bl_detection"),
    )

    return Simulation(general=general, material=material, wall_modeling=wall_modeling)


# ---------------------------------------------------------------------------
# <geometry>
# ---------------------------------------------------------------------------

def _parse_geometry(el: etree._Element) -> Geometry:
    baffle_el = el.find("baffle_parts")
    baffle_parts = _names(baffle_el) if baffle_el is not None else []

    ts_el = el.find("surface_mesh_optimization/triangle_splitting")
    ts_instances = []
    if ts_el is not None:
        for ti_el in ts_el.findall("triangle_splitting_instance"):
            ti_parts_el = ti_el.find("parts")
            ti_parts = _names(ti_parts_el) if ti_parts_el is not None else []
            ts_instances.append(TriangleSplittingInstance(
                name=_text(ti_el, "name"),
                active=_bool(ti_el, "active"),
                max_absolute_edge_length=_float(ti_el, "max_absolute_edge_length"),
                max_relative_edge_length=_float(ti_el, "max_relative_edge_length"),
                parts=ti_parts,
            ))
    triangle_splitting = TriangleSplitting(
        active=_bool(ts_el, "active"),
        max_absolute_edge_length=_float(ts_el, "max_absolute_edge_length"),
        max_relative_edge_length=_float(ts_el, "max_relative_edge_length"),
        triangle_splitting_instances=ts_instances,
    )

    dp_el = el.find("domain_part")
    instances = []
    for inst_el in dp_el.findall("domain_part_instance"):
        instances.append(DomainPartInstance(
            name=_text(inst_el, "name"),
            location=_text(inst_el, "location"),
            export_mesh=_bool(inst_el, "export_mesh"),
            bounding_range=_parse_bounding_range(inst_el.find("bounding_range")),
        ))

    # source_file vs source_files: detect which tag is present in the XML
    sfs_el = el.find("source_files")
    if sfs_el is not None:
        source_file = None
        source_files = _names(sfs_el)
    else:
        sf_el = el.find("source_file")
        source_file = sf_el.text.strip() if sf_el is not None and sf_el.text else None
        source_files = []

    return Geometry(
        source_file=source_file,
        source_files=source_files,
        baffle_parts=baffle_parts,
        domain_bounding_box=_parse_bounding_box(el.find("domain_bounding_box")),
        triangle_plinth=_bool(el, "triangle_plinth"),
        surface_mesh_optimization=SurfaceMeshOptimization(
            triangle_splitting=triangle_splitting
        ),
        domain_part=DomainPart(
            export_mesh=_bool(dp_el, "export_mesh"),
            domain_part_instances=instances,
        ),
    )


# ---------------------------------------------------------------------------
# <meshing>
# ---------------------------------------------------------------------------

def _parse_meshing(el: etree._Element) -> Meshing:
    gen_el = el.find("general")
    general = MeshingGeneral(
        coarsest_mesh_size=_float(gen_el, "coarsest_mesh_size"),
        mesh_preview=_bool(gen_el, "mesh_preview"),
        mesh_export=_bool(gen_el, "mesh_export"),
        refinement_level_transition_layers=_int(gen_el, "refinement_level_transition_layers"),
    )

    ref_el = el.find("refinement")

    # box refinement
    box_list = []
    box_el = ref_el.find("box")
    if box_el is not None:
        for inst_el in box_el.findall("box_instance"):
            box_list.append(BoxInstance(
                name=_text(inst_el, "name"),
                refinement_level=_int(inst_el, "refinement_level"),
                bounding_box=_parse_bounding_box(inst_el.find("bounding_box")),
            ))

    # offset refinement
    offset_list = []
    offset_el = ref_el.find("offset")
    if offset_el is not None:
        for inst_el in offset_el.findall("offset_instance"):
            parts_el = inst_el.find("parts")
            parts = _names(parts_el) if parts_el is not None else []
            offset_list.append(OffsetInstance(
                name=_text(inst_el, "name"),
                normal_distance=_float(inst_el, "normal_distance"),
                refinement_level=_int(inst_el, "refinement_level"),
                parts=parts,
            ))

    # custom refinement (GHN only)
    custom_list = []
    custom_el = ref_el.find("custom")
    if custom_el is not None:
        for inst_el in custom_el.findall("custom_instance"):
            parts_el = inst_el.find("parts")
            parts = _names(parts_el) if parts_el is not None else []
            custom_list.append(CustomInstance(
                name=_text(inst_el, "name"),
                refinement_level=_int(inst_el, "refinement_level"),
                parts=parts,
            ))

    # overset
    rotating_list = []
    overset_el = el.find("overset")
    if overset_el is not None:
        rotating_el = overset_el.find("rotating")
        if rotating_el is not None:
            for inst_el in rotating_el.findall("rotating_instance"):
                parts_el = inst_el.find("parts")
                parts = _names(parts_el) if parts_el is not None else []
                rotating_list.append(RotatingInstance(
                    name=_text(inst_el, "name"),
                    rpm=_float(inst_el, "rpm"),
                    center=_parse_xyz_pos(inst_el.find("center")),
                    axis=_parse_xyz_dir(inst_el.find("axis")),
                    parts=parts,
                ))

    return Meshing(
        general=general,
        refinement=Refinement(box=box_list, offset=offset_list, custom=custom_list),
        overset=Overset(rotating=rotating_list),
    )


# ---------------------------------------------------------------------------
# <boundary_conditions>
# ---------------------------------------------------------------------------

def _parse_fluid_bc(el: etree._Element):
    bc_type = _text(el, "type")

    if bc_type == "velocity":
        return FluidBCVelocity(
            type="velocity",
            velocity=_parse_xyz_dir(el.find("velocity")),
        )
    elif bc_type == "non_reflective_pressure":
        return FluidBCNonReflectivePressure(type="non_reflective_pressure")
    elif bc_type == "static":
        return FluidBCStatic(type="static")
    elif bc_type == "slip":
        return FluidBCSlip(type="slip")
    elif bc_type == "moving":
        return FluidBCMoving(
            type="moving",
            velocity=_parse_xyz_dir(el.find("velocity")),
        )
    elif bc_type == "rotating":
        return FluidBCRotating(
            type="rotating",
            rpm=_float(el, "rpm"),
            center=_parse_xyz_pos(el.find("center")),
            axis=_parse_xyz_dir(el.find("axis")),
        )
    else:
        raise ValueError(f"Unknown fluid_bc_settings type: {bc_type!r}")


def _parse_boundary_conditions(el: etree._Element) -> BoundaryConditions:
    inlet_list = []
    inlet_el = el.find("inlet")
    if inlet_el is not None:
        for inst_el in inlet_el.findall("inlet_instance"):
            parts_el = inst_el.find("parts")
            inlet_list.append(InletInstance(
                name=_text(inst_el, "name"),
                parts=_names(parts_el) if parts_el is not None else [],
                fluid_bc_settings=_parse_fluid_bc(inst_el.find("fluid_bc_settings")),
            ))

    outlet_list = []
    outlet_el = el.find("outlet")
    if outlet_el is not None:
        for inst_el in outlet_el.findall("outlet_instance"):
            parts_el = inst_el.find("parts")
            outlet_list.append(OutletInstance(
                name=_text(inst_el, "name"),
                parts=_names(parts_el) if parts_el is not None else [],
                fluid_bc_settings=_parse_fluid_bc(inst_el.find("fluid_bc_settings")),
            ))

    wall_list = []
    wall_el = el.find("wall")
    if wall_el is not None:
        for inst_el in wall_el.findall("wall_instance"):
            parts_el = inst_el.find("parts")
            roughness_text = _text_opt(inst_el, "roughness")
            wall_list.append(WallInstance(
                name=_text(inst_el, "name"),
                parts=_names(parts_el) if parts_el is not None else [],
                roughness=float(roughness_text) if roughness_text is not None else None,
                fluid_bc_settings=_parse_fluid_bc(inst_el.find("fluid_bc_settings")),
            ))

    return BoundaryConditions(inlet=inlet_list, outlet=outlet_list, wall=wall_list)


# ---------------------------------------------------------------------------
# <sources>
# ---------------------------------------------------------------------------

def _parse_sources(el: etree._Element) -> Sources:
    porous_list = []
    porous_el = el.find("porous")
    if porous_el is not None:
        for inst_el in porous_el.findall("porous_instance"):
            parts_el = inst_el.find("parts")
            axis_el = inst_el.find("porous_axis")
            porous_list.append(PorousInstance(
                name=_text(inst_el, "name"),
                inertial_resistance=_float(inst_el, "inertial_resistance"),
                viscous_resistance=_float(inst_el, "viscous_resistance"),
                porous_axis=PorousAxis(
                    x_dir=_float(axis_el, "x_dir"),
                    y_dir=_float(axis_el, "y_dir"),
                    z_dir=_float(axis_el, "z_dir"),
                ),
                parts=_names(parts_el) if parts_el is not None else [],
            ))

    turbulence_list = []
    turbulence_el = el.find("turbulence")
    if turbulence_el is not None:
        for inst_el in turbulence_el.findall("turbulence_instance"):
            point_el = inst_el.find("point")
            bb_el = inst_el.find("bounding_box")
            turbulence_list.append(TurbulenceInstance(
                name=_text(inst_el, "name"),
                num_eddies=_int(inst_el, "num_eddies"),
                length_scale=_float(inst_el, "length_scale"),
                turbulence_intensity=_float(inst_el, "turbulence_intensity"),
                point=TurbulencePoint(x_pos=_float(point_el, "x_pos")),
                bounding_box=TurbulenceBoundingBox(
                    y_min=_float(bb_el, "y_min"),
                    z_min=_float(bb_el, "z_min"),
                    y_max=_float(bb_el, "y_max"),
                    z_max=_float(bb_el, "z_max"),
                ),
            ))

    return Sources(porous=porous_list, turbulence=turbulence_list)


# ---------------------------------------------------------------------------
# <output>
# ---------------------------------------------------------------------------

def _parse_output_variables_full(el: etree._Element) -> OutputVariablesFull:
    def b(tag: str) -> bool:
        return _bool(el, tag)

    return OutputVariablesFull(
        pressure=b("pressure"),
        surface_normal=b("surface_normal"),
        pressure_std=b("pressure_std"),
        pressure_var=b("pressure_var"),
        time_avg_pressure=b("time_avg_pressure"),
        time_avg_velocity=b("time_avg_velocity"),
        time_avg_wall_shear_stress=b("time_avg_wall_shear_stress"),
        mesh_data=b("mesh_data"),
        velocity=b("velocity"),
        velocity_magnitude=b("velocity_magnitude"),
        wall_shear_stress=b("wall_shear_stress"),
        window_avg_pressure=b("window_avg_pressure"),
        window_avg_velocity=b("window_avg_velocity"),
        window_avg_wall_shear_stress=b("window_avg_wall_shear_stress"),
        mesh_displacement=b("mesh_displacement"),
        vorticity=b("vorticity"),
        vorticity_magnitude=b("vorticity_magnitude"),
        lambda_1=b("lambda_1"),
        lambda_2=b("lambda_2"),
        lambda_3=b("lambda_3"),
        q_criterion=b("q_criterion"),
        temperature=b("temperature"),
        time_avg_temperature=b("time_avg_temperature"),
        window_avg_temperature=b("window_avg_temperature"),
    )


def _parse_output_variables_surface(el: etree._Element) -> OutputVariablesSurface:
    def b(tag: str) -> bool:
        return _bool(el, tag)

    return OutputVariablesSurface(
        pressure=b("pressure"),
        surface_normal=b("surface_normal"),
        pressure_std=b("pressure_std"),
        pressure_var=b("pressure_var"),
        time_avg_pressure=b("time_avg_pressure"),
        time_avg_wall_shear_stress=b("time_avg_wall_shear_stress"),
        velocity=b("velocity"),
        velocity_magnitude=b("velocity_magnitude"),
        wall_shear_stress=b("wall_shear_stress"),
        window_avg_pressure=b("window_avg_pressure"),
        window_avg_wall_shear_stress=b("window_avg_wall_shear_stress"),
        mesh_displacement=b("mesh_displacement"),
        temperature=b("temperature"),
        time_avg_temperature=b("time_avg_temperature"),
        window_avg_temperature=b("window_avg_temperature"),
    )


def _parse_section_cut_output_variables(el: etree._Element) -> SectionCutOutputVariables:
    def b(tag: str) -> bool:
        return _bool(el, tag)

    return SectionCutOutputVariables(
        pressure=b("pressure"),
        pressure_std=b("pressure_std"),
        pressure_var=b("pressure_var"),
        time_avg_pressure=b("time_avg_pressure"),
        window_avg_pressure=b("window_avg_pressure"),
        velocity=b("velocity"),
        velocity_magnitude=b("velocity_magnitude"),
        time_avg_velocity=b("time_avg_velocity"),
        window_avg_velocity=b("window_avg_velocity"),
        mesh_displacement=b("mesh_displacement"),
        vorticity=b("vorticity"),
        vorticity_magnitude=b("vorticity_magnitude"),
        lambda_1=b("lambda_1"),
        lambda_2=b("lambda_2"),
        lambda_3=b("lambda_3"),
        q_criterion=b("q_criterion"),
        temperature=b("temperature"),
        time_avg_temperature=b("time_avg_temperature"),
        window_avg_temperature=b("window_avg_temperature"),
    )


def _parse_partial_surface_output_variables(el: etree._Element) -> PartialSurfaceOutputVariables:
    def b(tag: str) -> bool:
        return _bool(el, tag)

    return PartialSurfaceOutputVariables(
        pressure=b("pressure"),
        pressure_std=b("pressure_std"),
        pressure_var=b("pressure_var"),
        time_avg_pressure=b("time_avg_pressure"),
        window_avg_pressure=b("window_avg_pressure"),
        velocity=b("velocity"),
        velocity_magnitude=b("velocity_magnitude"),
        wall_shear_stress=b("wall_shear_stress"),
        time_avg_wall_shear_stress=b("time_avg_wall_shear_stress"),
        window_avg_wall_shear_stress=b("window_avg_wall_shear_stress"),
        surface_normal=b("surface_normal"),
        mesh_displacement=b("mesh_displacement"),
        temperature=b("temperature"),
        time_avg_temperature=b("time_avg_temperature"),
        window_avg_temperature=b("window_avg_temperature"),
    )


def _parse_partial_volume_output_variables(el: etree._Element) -> PartialVolumeOutputVariables:
    def b(tag: str) -> bool:
        return _bool(el, tag)

    return PartialVolumeOutputVariables(
        pressure=b("pressure"),
        pressure_std=b("pressure_std"),
        pressure_var=b("pressure_var"),
        time_avg_pressure=b("time_avg_pressure"),
        window_avg_pressure=b("window_avg_pressure"),
        velocity=b("velocity"),
        velocity_magnitude=b("velocity_magnitude"),
        time_avg_velocity=b("time_avg_velocity"),
        window_avg_velocity=b("window_avg_velocity"),
        mesh_displacement=b("mesh_displacement"),
        vorticity=b("vorticity"),
        vorticity_magnitude=b("vorticity_magnitude"),
        lambda_1=b("lambda_1"),
        lambda_2=b("lambda_2"),
        lambda_3=b("lambda_3"),
        q_criterion=b("q_criterion"),
        temperature=b("temperature"),
        time_avg_temperature=b("time_avg_temperature"),
        window_avg_temperature=b("window_avg_temperature"),
    )


def _parse_output(el: etree._Element) -> Output:
    gen_el = el.find("general")

    general = OutputGeneral(
        file_format=_parse_file_format(gen_el.find("file_format")),
        output_coarsening=_parse_output_coarsening(gen_el.find("output_coarsening")),
        time_varying_geometry_output=_bool(gen_el, "time_varying_geometry_output"),
        merge_output_files=_bool(gen_el, "merge_output_files"),
        delete_unmerged_output_files=_bool(gen_el, "delete_unmerged_output_files"),
        saved_states=_int(gen_el, "saved_states"),
        avg_start_coarsest_iteration=_int(gen_el, "avg_start_coarsest_iteration"),
        avg_window_size=_int(gen_el, "avg_window_size"),
        output_frequency=_int(gen_el, "output_frequency"),
        output_start_iteration=_int(gen_el, "output_start_iteration"),
        output_variables_full=_parse_output_variables_full(
            gen_el.find("output_variables_full")
        ),
        output_variables_surface=_parse_output_variables_surface(
            gen_el.find("output_variables_surface")
        ),
        bounding_box=_parse_bounding_box(gen_el.find("bounding_box")),
    )

    mrs_el = el.find("moment_reference_system")
    moment_ref = MomentReferenceSystem(
        type=_text(mrs_el, "Type"),
        origin=_parse_xyz_pos(mrs_el.find("origin")),
        roll_axis=_parse_xyz_dir(mrs_el.find("roll_axis")),
        pitch_axis=_parse_xyz_dir(mrs_el.find("pitch_axis")),
        yaw_axis=_parse_xyz_dir(mrs_el.find("yaw_axis")),
    )

    ac_el = el.find("aero_coefficients")
    caa_el = ac_el.find("coefficients_along_axis")
    eb_el = caa_el.find("export_bounds")
    passive_parts_el = ac_el.find("passive_parts")
    aero_coeff = AeroCoefficients(
        output_start_iteration=_int(ac_el, "output_start_iteration"),
        coefficients_parts=_bool(ac_el, "coefficients_parts"),
        reference_area_auto=_bool(ac_el, "reference_area_auto"),
        reference_area=_float(ac_el, "reference_area"),
        reference_length_auto=_bool(ac_el, "reference_length_auto"),
        reference_length=_float(ac_el, "reference_length"),
        coefficients_along_axis=CoefficientsAlongAxis(
            num_sections_x=_int(caa_el, "num_sections_x"),
            num_sections_y=_int(caa_el, "num_sections_y"),
            num_sections_z=_int(caa_el, "num_sections_z"),
            export_bounds=ExportBounds(
                active=_bool(eb_el, "active"),
                exclude_domain_parts=_bool(eb_el, "exclude_domain_parts"),
            ),
        ),
        passive_parts=_names(passive_parts_el) if passive_parts_el is not None else [],
    )

    # section_cut (GHN only)
    section_cut_list = []
    sc_el = el.find("section_cut")
    if sc_el is not None:
        for inst_el in sc_el.findall("section_cut_instance"):
            section_cut_list.append(SectionCutInstance(
                name=_text(inst_el, "name"),
                merge_output_files=_bool(inst_el, "merge_output_files"),
                delete_unmerged_output_files=_bool(inst_el, "delete_unmerged_output_files"),
                triangulation=_bool(inst_el, "triangulation"),
                file_format=_parse_file_format(inst_el.find("file_format")),
                axis=_parse_xyz_dir(inst_el.find("axis")),
                point=_parse_xyz_pos(inst_el.find("point")),
                bounding_box=_parse_bounding_box(inst_el.find("bounding_box")),
                output_frequency=_float(inst_el, "output_frequency"),
                output_start_iteration=_int(inst_el, "output_start_iteration"),
                output_variables=_parse_section_cut_output_variables(
                    inst_el.find("output_variables")
                ),
            ))

    # partial_surface
    ps_list = []
    ps_el = el.find("partial_surface")
    if ps_el is not None:
        for inst_el in ps_el.findall("partial_surface_instance"):
            parts_el = inst_el.find("parts")
            ps_list.append(PartialSurfaceInstance(
                name=_text(inst_el, "name"),
                parts=_names(parts_el) if parts_el is not None else [],
                merge_output_files=_bool(inst_el, "merge_output_files"),
                delete_unmerged_output_files=_bool(inst_el, "delete_unmerged_output_files"),
                file_format=_parse_file_format(inst_el.find("file_format")),
                output_frequency=_float(inst_el, "output_frequency"),
                output_start_iteration=_int(inst_el, "output_start_iteration"),
                output_variables=_parse_partial_surface_output_variables(
                    inst_el.find("output_variables")
                ),
            ))

    # partial_volume
    pv_list = []
    pv_el = el.find("partial_volume")
    if pv_el is not None:
        for inst_el in pv_el.findall("partial_volume_instance"):
            oc_el = inst_el.find("output_coarsening")
            pv_list.append(PartialVolumeInstance(
                name=_text(inst_el, "name"),
                merge_output_files=_bool(inst_el, "merge_output_files"),
                delete_unmerged_output_files=_bool(inst_el, "delete_unmerged_output_files"),
                file_format=_parse_file_format(inst_el.find("file_format")),
                output_frequency=_float(inst_el, "output_frequency"),
                output_start_iteration=_int(inst_el, "output_start_iteration"),
                bounding_box=_parse_bounding_box(inst_el.find("bounding_box")),
                output_variables=_parse_partial_volume_output_variables(
                    inst_el.find("output_variables")
                ),
                output_coarsening=_parse_output_coarsening(oc_el) if oc_el is not None else None,
            ))

    return Output(
        general=general,
        moment_reference_system=moment_ref,
        aero_coefficients=aero_coeff,
        section_cut=section_cut_list,
        partial_surface=ps_list,
        partial_volume=pv_list,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_ufx(source: Union[str, Path, io.IOBase, bytes]) -> UfxSolverDeck:
    """Parse an Ultrafluid XML solver deck into a UfxSolverDeck model.

    Args:
        source: Path to the .xml file (str/Path), a file-like object, or raw bytes.

    Returns:
        UfxSolverDeck Pydantic model.
    """
    if isinstance(source, bytes):
        root = etree.fromstring(source)
    elif isinstance(source, (str, Path)):
        tree = etree.parse(str(source))
        root = tree.getroot()
    else:
        # file-like object (e.g. io.BytesIO)
        tree = etree.parse(source)
        root = tree.getroot()

    return UfxSolverDeck(
        version=_parse_version(root.find("version")),
        simulation=_parse_simulation(root.find("simulation")),
        geometry=_parse_geometry(root.find("geometry")),
        meshing=_parse_meshing(root.find("meshing")),
        boundary_conditions=_parse_boundary_conditions(root.find("boundary_conditions")),
        sources=_parse_sources(root.find("sources")),
        output=_parse_output(root.find("output")),
    )
