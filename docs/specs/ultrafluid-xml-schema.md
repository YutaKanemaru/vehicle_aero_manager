# Ultrafluid XML Schema (Step 2 — Complete)

## Root Pydantic Model

```python
# app/ultrafluid/schema.py
class UfxSolverDeck(BaseModel):
    version: Version
    simulation: Simulation          # general, material, wall_modeling
    geometry: Geometry              # source_file, baffle, domain_bbox, domain_parts
    meshing: Meshing                # general, refinement (box/offset/custom), overset (rotating)
    boundary_conditions: BoundaryConditions  # inlet, outlet, static, wall
    sources: Sources                # porous, mrf, turbulence
    output: Output                  # general, moment_reference_system, aero_coefficients,
                                    # section_cut, probe_file, partial_surface, partial_volume,
                                    # monitoring_surface
```

## Known XML Structure (derived from sample files)

The root element is `<uFX_solver_deck>`. Key sub-structures:

```
<uFX_solver_deck>
  <version>
    <gui_version>          # str e.g. "2024"
    <solver_version>       # str e.g. "2024"
  <simulation>
    <general>
      <num_coarsest_iterations>   # int
      <mach_factor>               # float, default 1.0
      <num_ramp_up_iterations>    # int, default 200
      <parameter_preset>          # "default" | "fan_noise"
    <material>
      <name>                      # str e.g. "Air"
      <density>                   # float [kg/m³]
      <dynamic_viscosity>         # float [kg/(s·m)]
      <temperature>               # float [K]
      <specific_gas_constant>     # float [J/(kg·K)]
    <wall_modeling>
      <wall_model>                # "GLW" | "GWF" | "WangMoin" | "off", default "GLW"
      <coupling>                  # "adaptive_two-way" | "two-way" | "one-way" | "off"
      <transitional_bl_detection> # bool (GHN only)
  <geometry>
    <source_file>                 # str — single vehicle STL filename (`input.stl`); omitted when source_files is used
    <source_files>                # list of <name> — used when belt STL present (vehicle + belt) or multiple geometries;
                                  # vehicle entry is always `input.stl` (matches GET /download-stl)
    <baffle_parts>                # list of <name>
    <domain_bounding_box>         # x_min/x_max/y_min/y_max/z_min/z_max (Computed)
    <triangle_plinth>             # bool
    <surface_mesh_optimization>
      <triangle_splitting>
        <active>                  # bool — global ON/OFF
        <max_absolute_edge_length>  # float — global limit (0 = disabled)
        <max_relative_edge_length>  # float — global limit
        <triangle_splitting_instance>[]  # optional per-part overrides
          <name>, <active>, <max_absolute_edge_length>, <max_relative_edge_length>
          <parts><name>[]
    <domain_part>
      <export_mesh>               # bool
      <domain_part_instance>[]    # name, location ("z_min" etc.), bounding_range
  <meshing>
    <general>
      <coarsest_mesh_size>        # float (Computed from finest_resolution × 2^n_levels)
      <mesh_preview>              # bool
      <mesh_export>               # bool
      <refinement_level_transition_layers> # int default 8
    <refinement>
      <box><box_instance>[]       # name, refinement_level, bounding_box
      <offset><offset_instance>[] # name, normal_distance, refinement_level, [parts]
      <custom><custom_instance>[] # name, refinement_level, parts (GHN only)
    <overset>
      <rotating><rotating_instance>[]  # name, rpm, center(x/y/z), axis(x/y/z), parts
                                        # Aero: 4 wheels (VREV_*). GHN: empty <overset/>
  <boundary_conditions>
    <inlet><inlet_instance>[]     # name, parts, fluid_bc_settings (type: velocity)
    <outlet><outlet_instance>[]   # name, parts, fluid_bc_settings (type: non_reflective_pressure)
    <static/>                     # typically empty
    <wall><wall_instance>[]       # name, parts, [roughness], fluid_bc_settings
                                  # fluid_bc_settings type: static|slip|moving|rotating
  <sources>
    <porous><porous_instance>[]   # name, inertial_resistance, viscous_resistance,
                                  # porous_axis (x/y/z dir), parts
    <mrf/>                        # typically empty
    <turbulence><turbulence_instance>[]  # name, num_eddies, length_scale,
                                          # turbulence_intensity, point, bounding_box
                                          # Aero only; GHN has no <turbulence>
  <output>
    <general>                     # file_format, output_coarsening, output_variables_full/surface,
                                  # avg_start/window_size/frequency, bounding_box
    <moment_reference_system>     # origin, roll/pitch/yaw axis (no Type field — not in official docs)
    <aero_coefficients>           # reference_area/length, coefficients_along_axis, passive_parts
    <section_cut><section_cut_instance>[]  # GHN specific — high-frequency transient output
    <probe_file><probe_file_instance>[]    # optional — probe locations loaded from CSV
    <partial_surface><partial_surface_instance>[]
    <partial_volume><partial_volume_instance>[]
    <monitoring_surface/>
```

## Aero vs GHN Differences

| Element | Aero | GHN |
|---|---|---|
| `meshing.refinement.custom` | absent | present (VREF_RL7 etc.) |
| `meshing.overset.rotating` | 4 wheels (VREV_*) | empty `<overset/>` |
| `boundary_conditions.wall` | Belt (moving) + wheel (rotating) | static/slip only |
| `sources.turbulence` | present (tg_ground, tg_body) | absent |
| `output.section_cut` | absent | present (high-freq transient) |
| `simulation.wall_modeling.transitional_bl_detection` | absent | present |

## Known Enum Values (from official docs & sample files)

| Field | Valid Values | Default |
|---|---|---|
| `parameter_preset` | `"default"`, `"fan_noise"` | `"default"` |
| `wall_model` | `"GLW"`, `"GWF"`, `"WangMoin"`, `"off"` | `"GLW"` |
| `coupling` | `"adaptive_two-way"`, `"two-way"`, `"one-way"`, `"off"` | `"adaptive_two-way"` |
| `pressure_gradient` | `"favorable"`, `"adverse"`, `"full"`, `"off"` | `"adverse"` |
| `domain_part_instance.location` | `"z_min"`, `"x_min"`, `"x_max"`, `"y_min"`, `"y_max"`, `"z_max"` | — |
| `fluid_bc_settings.type` | `"velocity"`, `"non_reflective_pressure"`, `"static"`, `"slip"`, `"moving"`, `"rotating"` | — |

## Field Classification

| Classification | Description | Example |
|---|---|---|
| `Fixed` | Value defined in a Template, does not change per geometry | `simulation.general.*`, `boundary_conditions.inlet.velocity` |
| `Computed` | Derived from STL geometry analysis (streaming ASCII parser + NumPy) | `geometry.domain_bounding_box`, `meshing.overset.rotating` |
| `UserInput` | Set explicitly by the engineer via UI | `sources.porous.resistance` |

## XML Generation Pipeline

```
Template (JSON/Fixed) + GeometrySet (STL/Computed) + UserInput
    ↓
Compute Engine (trimesh + NumPy)
    ↓
Pydantic model assembly + validation (UfxSolverDeck)
    ↓
lxml.etree serialization
    ↓
Ultrafluid XML file
```

## XML Serialization Rules

> **Reference**: All XML structure, tag naming, field semantics, and parameter values must conform to the official **[Altair ultraFluidX User Guide](https://help.altair.com/hwcfdsolvers/ufx/index.htm)**. When in doubt about an XML element's name, structure, or valid values, consult the user guide first before referring to sample files.

- Use `lxml.etree` for all XML generation — never use `xml.etree.ElementTree`
- Implement a `to_xml()` method or standalone serializer in `app/ultrafluid/serializer.py`
- Implement a `from_xml()` parser in `app/ultrafluid/parser.py`
- Round-trip test required: `parse(serialize(model)) == model`
- XML tag names are snake_case (e.g. `<domain_bounding_box>`, `<num_coarsest_iterations>`)
- Lists of instances use a repeated child pattern: `<box><box_instance>...</box_instance><box_instance>...</box_instance></box>`
- Boolean values are serialized as lowercase strings: `"true"` / `"false"`
- Float values may use scientific notation: e.g. `1.8194e-05`
- Empty optional sections must be serialized as self-closing tags: `<mrf/>`, `<static/>`
- Sample files reference: `docs/samples/aero/AUR_v1.2_EXT_1.99_corrected.xml` (Aero), `docs/samples/GHN/CX1_v1.2_GHN_cut_plane_volume_corrected.xml` (GHN)
