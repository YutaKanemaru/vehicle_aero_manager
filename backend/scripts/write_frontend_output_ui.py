"""
Write updated frontend files for the Output, Meshing, and BC sections.
This adds:
  - Output variables checkboxes (full + surface)
  - Partial surfaces dynamic list
  - Partial volumes dynamic list
  - Section cuts dynamic list
  - Offset refinement dynamic list (with Add Defaults button)
  - Custom refinement dynamic list
  - Porous coefficients template-level dynamic list
"""

from pathlib import Path

REPO = Path(__file__).parent.parent.parent
FRONTEND_SRC = REPO / "frontend" / "src"
HOOKS = FRONTEND_SRC / "hooks" / "useTemplateSettingsForm.ts"
FORM = FRONTEND_SRC / "components" / "templates" / "TemplateSettingsForm.tsx"

# ============================================================
# useTemplateSettingsForm.ts
# ============================================================

HOOK_CONTENT = r'''/**
 * Shared form logic for Template create / version create modals.
 */

// ---- utilities ---------------------------------------------------------------

export function splitList(s: string): string[] {
  return s
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

export function joinList(arr: string[] | undefined | null): string {
  return (arr ?? []).join(", ");
}

// ---- nested item types -------------------------------------------------------

export interface OutputVarsFull {
  pressure: boolean;
  surface_normal: boolean;
  pressure_std: boolean;
  pressure_var: boolean;
  time_avg_pressure: boolean;
  time_avg_velocity: boolean;
  time_avg_wall_shear_stress: boolean;
  mesh_data: boolean;
  velocity: boolean;
  velocity_magnitude: boolean;
  wall_shear_stress: boolean;
  window_avg_pressure: boolean;
  window_avg_velocity: boolean;
  window_avg_wall_shear_stress: boolean;
  mesh_displacement: boolean;
  vorticity: boolean;
  vorticity_magnitude: boolean;
  lambda_1: boolean;
  lambda_2: boolean;
  lambda_3: boolean;
  q_criterion: boolean;
  temperature: boolean;
  time_avg_temperature: boolean;
  window_avg_temperature: boolean;
}

export interface OutputVarsSurface {
  pressure: boolean;
  surface_normal: boolean;
  pressure_std: boolean;
  pressure_var: boolean;
  time_avg_pressure: boolean;
  time_avg_wall_shear_stress: boolean;
  velocity: boolean;
  velocity_magnitude: boolean;
  wall_shear_stress: boolean;
  window_avg_pressure: boolean;
  window_avg_wall_shear_stress: boolean;
  mesh_displacement: boolean;
  temperature: boolean;
  time_avg_temperature: boolean;
  window_avg_temperature: boolean;
}

export interface OutputVarsPartialSurface {
  pressure: boolean;
  pressure_std: boolean;
  pressure_var: boolean;
  time_avg_pressure: boolean;
  window_avg_pressure: boolean;
  velocity: boolean;
  velocity_magnitude: boolean;
  wall_shear_stress: boolean;
  time_avg_wall_shear_stress: boolean;
  window_avg_wall_shear_stress: boolean;
  surface_normal: boolean;
  mesh_displacement: boolean;
  temperature: boolean;
  time_avg_temperature: boolean;
  window_avg_temperature: boolean;
}

export interface OutputVarsPartialVolume {
  pressure: boolean;
  pressure_std: boolean;
  pressure_var: boolean;
  time_avg_pressure: boolean;
  window_avg_pressure: boolean;
  velocity: boolean;
  velocity_magnitude: boolean;
  time_avg_velocity: boolean;
  window_avg_velocity: boolean;
  mesh_displacement: boolean;
  vorticity: boolean;
  vorticity_magnitude: boolean;
  lambda_1: boolean;
  lambda_2: boolean;
  lambda_3: boolean;
  q_criterion: boolean;
  temperature: boolean;
  time_avg_temperature: boolean;
  window_avg_temperature: boolean;
}

export interface OutputVarsSectionCut {
  pressure: boolean;
  pressure_std: boolean;
  pressure_var: boolean;
  time_avg_pressure: boolean;
  window_avg_pressure: boolean;
  velocity: boolean;
  velocity_magnitude: boolean;
  time_avg_velocity: boolean;
  window_avg_velocity: boolean;
  mesh_displacement: boolean;
  vorticity: boolean;
  vorticity_magnitude: boolean;
  lambda_1: boolean;
  lambda_2: boolean;
  lambda_3: boolean;
  q_criterion: boolean;
  temperature: boolean;
  time_avg_temperature: boolean;
  window_avg_temperature: boolean;
}

export interface PartialSurfaceFormItem {
  name: string;
  output_start_time: number | null;
  output_interval: number | null;
  file_format_ensight: boolean;
  file_format_h3d: boolean;
  merge_output: boolean;
  delete_unmerged: boolean;
  include_parts: string;           // comma-separated
  exclude_parts: string;           // comma-separated
  baffle_export_option: "front_only" | "back_only" | "both" | "";
  output_variables: OutputVarsPartialSurface;
}

export interface PartialVolumeFormItem {
  name: string;
  output_start_time: number | null;
  output_interval: number | null;
  file_format_ensight: boolean;
  file_format_h3d: boolean;
  output_coarsening_active: boolean;
  coarsest_target_refinement_level: number;
  coarsen_by_num_refinement_levels: number;
  merge_output: boolean;
  delete_unmerged: boolean;
  bbox_mode: "from_meshing_box" | "around_parts" | "user_defined";
  bbox_source_box_name: string;
  bbox_source_parts: string;       // comma-separated
  bbox: string;                    // "xmin,xmax,ymin,ymax,zmin,zmax"
  output_variables: OutputVarsPartialVolume;
}

export interface SectionCutFormItem {
  name: string;
  output_start_time: number | null;
  output_interval: number | null;
  file_format_ensight: boolean;
  file_format_h3d: boolean;
  merge_output: boolean;
  delete_unmerged: boolean;
  triangulation: boolean;
  axis_x: number;
  axis_y: number;
  axis_z: number;
  point_x: number;
  point_y: number;
  point_z: number;
  bbox: string;                    // "xmin,xmax,ymin,ymax,zmin,zmax" or ""
  output_variables: OutputVarsSectionCut;
}

export interface OffsetRefinementFormItem {
  name: string;
  level: number;
  normal_distance: number;
  parts: string;                   // comma-separated (empty = body offset)
}

export interface CustomRefinementFormItem {
  name: string;
  level: number;
  parts: string;                   // comma-separated
}

export interface PorousCoeffFormItem {
  part_name: string;
  inertial_resistance: number;
  viscous_resistance: number;
}

// ---- defaults ----------------------------------------------------------------

const DEFAULT_OV_FULL: OutputVarsFull = {
  pressure: false, surface_normal: false, pressure_std: false, pressure_var: false,
  time_avg_pressure: false, time_avg_velocity: false, time_avg_wall_shear_stress: false,
  mesh_data: false, velocity: false, velocity_magnitude: false, wall_shear_stress: false,
  window_avg_pressure: false, window_avg_velocity: false, window_avg_wall_shear_stress: false,
  mesh_displacement: false, vorticity: false, vorticity_magnitude: false,
  lambda_1: false, lambda_2: false, lambda_3: false, q_criterion: false,
  temperature: false, time_avg_temperature: false, window_avg_temperature: false,
};

const DEFAULT_OV_SURFACE: OutputVarsSurface = {
  pressure: false, surface_normal: false, pressure_std: false, pressure_var: false,
  time_avg_pressure: false, time_avg_wall_shear_stress: false,
  velocity: false, velocity_magnitude: false, wall_shear_stress: false,
  window_avg_pressure: false, window_avg_wall_shear_stress: false,
  mesh_displacement: false, temperature: false, time_avg_temperature: false,
  window_avg_temperature: false,
};

const DEFAULT_OV_PS: OutputVarsPartialSurface = {
  pressure: false, pressure_std: false, pressure_var: false,
  time_avg_pressure: false, window_avg_pressure: false,
  velocity: false, velocity_magnitude: false, wall_shear_stress: false,
  time_avg_wall_shear_stress: false, window_avg_wall_shear_stress: false,
  surface_normal: false, mesh_displacement: false, temperature: false,
  time_avg_temperature: false, window_avg_temperature: false,
};

const DEFAULT_OV_PV: OutputVarsPartialVolume = {
  pressure: false, pressure_std: false, pressure_var: false,
  time_avg_pressure: false, window_avg_pressure: false,
  velocity: false, velocity_magnitude: false,
  time_avg_velocity: false, window_avg_velocity: false,
  mesh_displacement: false, vorticity: false, vorticity_magnitude: false,
  lambda_1: false, lambda_2: false, lambda_3: false, q_criterion: false,
  temperature: false, time_avg_temperature: false, window_avg_temperature: false,
};

const DEFAULT_OV_SC: OutputVarsSectionCut = {
  pressure: false, pressure_std: false, pressure_var: false,
  time_avg_pressure: false, window_avg_pressure: false,
  velocity: false, velocity_magnitude: false,
  time_avg_velocity: false, window_avg_velocity: false,
  mesh_displacement: false, vorticity: false, vorticity_magnitude: false,
  lambda_1: false, lambda_2: false, lambda_3: false, q_criterion: false,
  temperature: false, time_avg_temperature: false, window_avg_temperature: false,
};

// ---- flat form defaults -------------------------------------------------------

export const FORM_DEFAULTS = {
  // ── Simulation parameters ─────────────────────────────────────────────
  inflow_velocity: 38.88,
  density: 1.2041,
  dynamic_viscosity: 0.000018194,
  temperature: 20.0,
  specific_gas_constant: 287.05,
  mach_factor: 2.0,
  num_ramp_up_iter: 200,
  coarsest_voxel_size: 0.192,
  number_of_resolution: 7,
  simulation_time: 2.0,
  simulation_time_FP: 30.0,
  start_averaging_time: 1.5,
  avg_window_size: 0.3,
  yaw_angle: 0.0,
  temperature_degree: true,
  simulation_time_with_FP: false,

  // ── Meshing ───────────────────────────────────────────────────────────
  triangle_splitting: true,
  triangle_splitting_specify_part: false,
  max_relative_edge_length: 9.0,
  refinement_level_transition_layers: 8,
  domain_bounding_box_relative: true,
  box_offset_relative: true,
  box_refinement_porous: true,
  bbox_xmin: -5.0,
  bbox_xmax: 15.0,
  bbox_ymin: -12.0,
  bbox_ymax: 12.0,
  bbox_zmin: 0.0,
  bbox_zmax: 20.0,
  // Offset refinement dynamic list
  offset_refinements: [] as OffsetRefinementFormItem[],
  // Custom refinement dynamic list
  custom_refinements: [] as CustomRefinementFormItem[],

  // ── Boundary conditions — ground ──────────────────────────────────────
  ground_height_mode: "from_geometry" as "from_geometry" | "absolute",
  ground_height_absolute: 0.0,
  ground_patch_active: true,
  ground_mode: "rotating_belt_5" as
    | "static" | "rotating_belt_1" | "rotating_belt_5" | "full_moving",
  overset_wheels: true,
  bl_suction_apply: true,
  bl_suction_no_slip_xmin_pos: null as number | null,
  bl_suction_from_belt_xmin: true,
  bl_suction_xmin_offset: 0.0,
  belt5_wheel_loc_auto: true,
  belt5_narrow_fallback: false,
  belt5_narrow_min_gap: 0.3,
  belt5_center_pos: "at_wheelbase_center" as "at_wheelbase_center" | "user_specified",
  belt5_center_x: null as number | null,
  belt5_wheel_size_x: 0.4,
  belt5_wheel_size_y: 0.3,
  belt5_center_size_x: 0.4,
  belt5_center_size_y: 0.3,
  belt5_include_wheel_forces: true,
  belt1_size_x: 0.4,
  belt1_size_y: 1.2,
  apply_static_ground_refinement: true,

  // Porous coefficients at template level
  porous_coefficients: [] as PorousCoeffFormItem[],

  // ── Boundary conditions — turbulence generator ────────────────────────
  tg_enable_ground: true,
  tg_enable_body: true,
  tg_ground_num_eddies: 800,
  tg_ground_intensity: 0.05,
  tg_body_num_eddies: 800,
  tg_body_intensity: 0.01,

  // ── Compute flags ─────────────────────────────────────────────────────
  compute_rotate_wheels: true,
  compute_porous_media: true,
  compute_turbulence_generator: true,
  compute_moving_ground: true,
  compute_adjust_ride_height: false,

  // ── Output — full data ────────────────────────────────────────────────
  fd_output_start_time: null as number | null,
  fd_output_interval: null as number | null,
  fd_format_ensight: false,
  fd_format_h3d: true,
  fd_coarsening_active: false,
  fd_coarsest_target_rl: 3,
  fd_coarsen_by_num_rl: 0,
  fd_merge_output: true,
  fd_delete_unmerged: true,
  fd_bbox_mode: "from_meshing_box" as "from_meshing_box" | "user_defined",
  fd_bbox_source_box: "",
  fd_bbox_xmin: -10.0,
  fd_bbox_xmax: 30.0,
  fd_bbox_ymin: -15.0,
  fd_bbox_ymax: 15.0,
  fd_bbox_zmin: 0.0,
  fd_bbox_zmax: 8.0,
  // Output variables
  output_variables_full: { ...DEFAULT_OV_FULL } as OutputVarsFull,
  output_variables_surface: { ...DEFAULT_OV_SURFACE } as OutputVarsSurface,

  // ── Output — aero coefficients ────────────────────────────────────────
  ac_ref_area_auto: true,
  ac_ref_area: 2.4,
  ac_ref_length_auto: true,
  ac_ref_length: 2.7,
  ac_along_axis_active: false,
  ac_num_sections_x: 100,
  ac_num_sections_y: 0,
  ac_num_sections_z: 0,
  ac_export_bounds_active: true,
  ac_export_bounds_exclude_domain: true,

  // ── Output — dynamic lists ────────────────────────────────────────────
  partial_surfaces: [] as PartialSurfaceFormItem[],
  partial_volumes: [] as PartialVolumeFormItem[],
  section_cuts: [] as SectionCutFormItem[],

  // ── Target names (comma-separated for list fields) ────────────────────
  tn_wheel: "",
  tn_rim: "",
  tn_porous: "",
  tn_car_bounding_box: "",
  tn_baffle: "",
  tn_triangle_splitting: "",
  tn_windtunnel: "",
  tn_wt_fr_lh: "",
  tn_wt_fr_rh: "",
  tn_wt_rr_lh: "",
  tn_wt_rr_rh: "",
  tn_osm_fr_lh: "",
  tn_osm_fr_rh: "",
  tn_osm_rr_lh: "",
  tn_osm_rr_rh: "",
  tn_tire_roughness: 0.0,
};

export type FormValues = typeof FORM_DEFAULTS;

// ---- helpers -----------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ovFull(src: any): OutputVarsFull {
  if (!src) return { ...DEFAULT_OV_FULL };
  return Object.fromEntries(
    Object.keys(DEFAULT_OV_FULL).map((k) => [k, src[k] ?? false])
  ) as OutputVarsFull;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ovSurface(src: any): OutputVarsSurface {
  if (!src) return { ...DEFAULT_OV_SURFACE };
  return Object.fromEntries(
    Object.keys(DEFAULT_OV_SURFACE).map((k) => [k, src[k] ?? false])
  ) as OutputVarsSurface;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ovPS(src: any): OutputVarsPartialSurface {
  if (!src) return { ...DEFAULT_OV_PS };
  return Object.fromEntries(
    Object.keys(DEFAULT_OV_PS).map((k) => [k, src[k] ?? false])
  ) as OutputVarsPartialSurface;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ovPV(src: any): OutputVarsPartialVolume {
  if (!src) return { ...DEFAULT_OV_PV };
  return Object.fromEntries(
    Object.keys(DEFAULT_OV_PV).map((k) => [k, src[k] ?? false])
  ) as OutputVarsPartialVolume;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ovSC(src: any): OutputVarsSectionCut {
  if (!src) return { ...DEFAULT_OV_SC };
  return Object.fromEntries(
    Object.keys(DEFAULT_OV_SC).map((k) => [k, src[k] ?? false])
  ) as OutputVarsSectionCut;
}

function bboxToStr(b: number[] | null | undefined): string {
  if (Array.isArray(b) && b.length === 6) return b.join(",");
  return "";
}

function strToBbox(s: string): number[] | null {
  if (!s.trim()) return null;
  const parts = s.split(",").map(Number);
  if (parts.length === 6 && parts.every((v) => !isNaN(v))) return parts;
  return null;
}

// ---- populate form values from existing TemplateSettings JSON ----------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function valuesFromSettings(settings: any): FormValues {
  const sp = settings?.simulation_parameter ?? {};
  const so = settings?.setup_option ?? {};
  const m = so?.meshing ?? {};
  const gc = so?.boundary_condition?.ground ?? {};
  const bl = gc?.bl_suction ?? {};
  const b5 = gc?.belt5 ?? {};
  const b1 = gc?.belt1 ?? {};
  const tg = so?.boundary_condition?.turbulence_generator ?? {};
  const cp = so?.compute ?? {};
  const setup = settings?.setup ?? {};
  const bbox = setup?.domain_bounding_box ?? [-5, 15, -12, 12, 0, 20];
  const tn = settings?.target_names ?? {};
  const out = settings?.output ?? {};
  const fd = out?.full_data ?? {};
  const ac = out?.aero_coefficients ?? {};
  const fdBbox = Array.isArray(fd?.bbox) && fd.bbox.length === 6
    ? fd.bbox : [-10, 30, -15, 15, 0, 8];

  // Offset & custom refinements from setup.meshing
  const meshingSetup = setup?.meshing ?? {};
  const offsetRefinements: OffsetRefinementFormItem[] = Object.entries(
    meshingSetup.offset_refinement ?? {}
  ).map(([name, v]: [string, any]) => ({
    name,
    level: v.level ?? 6,
    normal_distance: v.normal_distance ?? 0.05,
    parts: joinList(v.parts),
  }));
  const customRefinements: CustomRefinementFormItem[] = Object.entries(
    meshingSetup.custom_refinement ?? {}
  ).map(([name, v]: [string, any]) => ({
    name,
    level: v.level ?? 7,
    parts: joinList(v.parts),
  }));

  // Partial surfaces, volumes, section cuts
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialSurfaces: PartialSurfaceFormItem[] = (out?.partial_surfaces ?? []).map((ps: any) => ({
    name: ps.name ?? "partial_surface",
    output_start_time: ps.output_start_time ?? null,
    output_interval: ps.output_interval ?? null,
    file_format_ensight: ps.file_format_ensight ?? false,
    file_format_h3d: ps.file_format_h3d ?? true,
    merge_output: ps.merge_output ?? true,
    delete_unmerged: ps.delete_unmerged ?? true,
    include_parts: joinList(ps.include_parts),
    exclude_parts: joinList(ps.exclude_parts),
    baffle_export_option: ps.baffle_export_option ?? "",
    output_variables: ovPS(ps.output_variables),
  }));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialVolumes: PartialVolumeFormItem[] = (out?.partial_volumes ?? []).map((pv: any) => ({
    name: pv.name ?? "partial_volume",
    output_start_time: pv.output_start_time ?? null,
    output_interval: pv.output_interval ?? null,
    file_format_ensight: pv.file_format_ensight ?? false,
    file_format_h3d: pv.file_format_h3d ?? true,
    output_coarsening_active: pv.output_coarsening_active ?? false,
    coarsest_target_refinement_level: pv.coarsest_target_refinement_level ?? 3,
    coarsen_by_num_refinement_levels: pv.coarsen_by_num_refinement_levels ?? 0,
    merge_output: pv.merge_output ?? true,
    delete_unmerged: pv.delete_unmerged ?? true,
    bbox_mode: pv.bbox_mode ?? "user_defined",
    bbox_source_box_name: pv.bbox_source_box_name ?? "",
    bbox_source_parts: joinList(pv.bbox_source_parts),
    bbox: bboxToStr(pv.bbox),
    output_variables: ovPV(pv.output_variables),
  }));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sectionCuts: SectionCutFormItem[] = (out?.section_cuts ?? []).map((sc: any) => ({
    name: sc.name ?? "section_cut",
    output_start_time: sc.output_start_time ?? null,
    output_interval: sc.output_interval ?? null,
    file_format_ensight: sc.file_format_ensight ?? false,
    file_format_h3d: sc.file_format_h3d ?? true,
    merge_output: sc.merge_output ?? true,
    delete_unmerged: sc.delete_unmerged ?? true,
    triangulation: sc.triangulation ?? false,
    axis_x: sc.axis_x ?? 0.0,
    axis_y: sc.axis_y ?? 0.0,
    axis_z: sc.axis_z ?? 1.0,
    point_x: sc.point_x ?? 0.0,
    point_y: sc.point_y ?? 0.0,
    point_z: sc.point_z ?? 0.0,
    bbox: bboxToStr(sc.bbox),
    output_variables: ovSC(sc.output_variables),
  }));

  // Porous coefficients
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const porousCoeffs: PorousCoeffFormItem[] = (settings?.porous_coefficients ?? []).map((p: any) => ({
    part_name: p.part_name ?? "",
    inertial_resistance: p.inertial_resistance ?? 0.0,
    viscous_resistance: p.viscous_resistance ?? 0.0,
  }));

  return {
    inflow_velocity: sp.inflow_velocity ?? 38.88,
    density: sp.density ?? 1.2041,
    dynamic_viscosity: sp.dynamic_viscosity ?? 0.000018194,
    temperature: sp.temperature ?? 20.0,
    specific_gas_constant: sp.specific_gas_constant ?? 287.05,
    mach_factor: sp.mach_factor ?? 2.0,
    num_ramp_up_iter: sp.num_ramp_up_iter ?? 200,
    coarsest_voxel_size: sp.coarsest_voxel_size ?? 0.192,
    number_of_resolution: sp.number_of_resolution ?? 7,
    simulation_time: sp.simulation_time ?? 2.0,
    simulation_time_FP: sp.simulation_time_FP ?? 30.0,
    start_averaging_time: sp.start_averaging_time ?? 1.5,
    avg_window_size: sp.avg_window_size ?? 0.3,
    yaw_angle: sp.yaw_angle ?? 0.0,
    temperature_degree: so?.simulation?.temperature_degree ?? true,
    simulation_time_with_FP: so?.simulation?.simulation_time_with_FP ?? false,

    triangle_splitting: m.triangle_splitting ?? true,
    triangle_splitting_specify_part: m.triangle_splitting_specify_part ?? false,
    max_relative_edge_length: m.max_relative_edge_length ?? 9.0,
    refinement_level_transition_layers: m.refinement_level_transition_layers ?? 8,
    domain_bounding_box_relative: m.domain_bounding_box_relative ?? true,
    box_offset_relative: m.box_offset_relative ?? true,
    box_refinement_porous: m.box_refinement_porous ?? true,
    bbox_xmin: bbox[0] ?? -5.0,
    bbox_xmax: bbox[1] ?? 15.0,
    bbox_ymin: bbox[2] ?? -12.0,
    bbox_ymax: bbox[3] ?? 12.0,
    bbox_zmin: bbox[4] ?? 0.0,
    bbox_zmax: bbox[5] ?? 20.0,
    offset_refinements: offsetRefinements,
    custom_refinements: customRefinements,

    ground_height_mode: gc.ground_height_mode ?? "from_geometry",
    ground_height_absolute: gc.ground_height_absolute ?? 0.0,
    ground_patch_active: gc.ground_patch_active ?? true,
    ground_mode: gc.ground_mode ?? "rotating_belt_5",
    overset_wheels: gc.overset_wheels ?? true,
    bl_suction_apply: bl.apply ?? true,
    bl_suction_no_slip_xmin_pos: bl.no_slip_xmin_pos ?? null,
    bl_suction_from_belt_xmin: bl.no_slip_xmin_from_belt_xmin ?? true,
    bl_suction_xmin_offset: bl.bl_xmin_offset ?? 0.0,
    belt5_wheel_loc_auto: b5.wheel_belt_location_auto ?? true,
    belt5_narrow_fallback: b5.narrow_car_fallback?.enabled ?? false,
    belt5_narrow_min_gap: b5.narrow_car_fallback?.min_belt_gap ?? 0.3,
    belt5_center_pos: b5.center_belt_position ?? "at_wheelbase_center",
    belt5_center_x: b5.center_belt_x_pos ?? null,
    belt5_wheel_size_x: b5.belt_size_wheel?.x ?? 0.4,
    belt5_wheel_size_y: b5.belt_size_wheel?.y ?? 0.3,
    belt5_center_size_x: b5.belt_size_center?.x ?? 0.4,
    belt5_center_size_y: b5.belt_size_center?.y ?? 0.3,
    belt5_include_wheel_forces: b5.include_wheel_belt_forces ?? true,
    belt1_size_x: b1.belt_size?.x ?? 0.4,
    belt1_size_y: b1.belt_size?.y ?? 1.2,
    apply_static_ground_refinement: gc.apply_static_ground_refinement ?? true,
    porous_coefficients: porousCoeffs,

    tg_enable_ground: tg.enable_ground_tg ?? true,
    tg_enable_body: tg.enable_body_tg ?? true,
    tg_ground_num_eddies: tg.ground_tg_num_eddies ?? 800,
    tg_ground_intensity: tg.ground_tg_intensity ?? 0.05,
    tg_body_num_eddies: tg.body_tg_num_eddies ?? 800,
    tg_body_intensity: tg.body_tg_intensity ?? 0.01,

    compute_rotate_wheels: cp.rotate_wheels ?? true,
    compute_porous_media: cp.porous_media ?? true,
    compute_turbulence_generator: cp.turbulence_generator ?? true,
    compute_moving_ground: cp.moving_ground ?? true,
    compute_adjust_ride_height: cp.adjust_ride_height ?? false,

    fd_output_start_time: fd.output_start_time ?? null,
    fd_output_interval: fd.output_interval ?? null,
    fd_format_ensight: fd.file_format_ensight ?? false,
    fd_format_h3d: fd.file_format_h3d ?? true,
    fd_coarsening_active: fd.output_coarsening_active ?? false,
    fd_coarsest_target_rl: fd.coarsest_target_refinement_level ?? 3,
    fd_coarsen_by_num_rl: fd.coarsen_by_num_refinement_levels ?? 0,
    fd_merge_output: fd.merge_output ?? true,
    fd_delete_unmerged: fd.delete_unmerged ?? true,
    fd_bbox_mode: fd.bbox_mode ?? "from_meshing_box",
    fd_bbox_source_box: fd.bbox_source_box_name ?? "",
    fd_bbox_xmin: fdBbox[0],
    fd_bbox_xmax: fdBbox[1],
    fd_bbox_ymin: fdBbox[2],
    fd_bbox_ymax: fdBbox[3],
    fd_bbox_zmin: fdBbox[4],
    fd_bbox_zmax: fdBbox[5],
    output_variables_full: ovFull(fd.output_variables_full),
    output_variables_surface: ovSurface(fd.output_variables_surface),

    ac_ref_area_auto: ac.reference_area_auto ?? true,
    ac_ref_area: ac.reference_area ?? 2.4,
    ac_ref_length_auto: ac.reference_length_auto ?? true,
    ac_ref_length: ac.reference_length ?? 2.7,
    ac_along_axis_active: ac.coefficients_along_axis_active ?? false,
    ac_num_sections_x: ac.num_sections_x ?? 100,
    ac_num_sections_y: ac.num_sections_y ?? 0,
    ac_num_sections_z: ac.num_sections_z ?? 0,
    ac_export_bounds_active: ac.export_bounds_active ?? true,
    ac_export_bounds_exclude_domain: ac.export_bounds_exclude_domain_parts ?? true,

    partial_surfaces: partialSurfaces,
    partial_volumes: partialVolumes,
    section_cuts: sectionCuts,

    tn_wheel: joinList(tn.wheel),
    tn_rim: joinList(tn.rim),
    tn_porous: joinList(tn.porous),
    tn_car_bounding_box: joinList(tn.car_bounding_box),
    tn_baffle: joinList(tn.baffle),
    tn_triangle_splitting: joinList(tn.triangle_splitting),
    tn_windtunnel: joinList(tn.windtunnel),
    tn_wt_fr_lh: tn.wheel_tire_fr_lh ?? "",
    tn_wt_fr_rh: tn.wheel_tire_fr_rh ?? "",
    tn_wt_rr_lh: tn.wheel_tire_rr_lh ?? "",
    tn_wt_rr_rh: tn.wheel_tire_rr_rh ?? "",
    tn_osm_fr_lh: tn.overset_fr_lh ?? "",
    tn_osm_fr_rh: tn.overset_fr_rh ?? "",
    tn_osm_rr_lh: tn.overset_rr_lh ?? "",
    tn_osm_rr_rh: tn.overset_rr_rh ?? "",
    tn_tire_roughness: tn.tire_roughness ?? 0.0,
  };
}

// ---- build TemplateSettings JSON from flat form values -----------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function buildSettings(values: FormValues, existingSettings?: any): object {
  const fdBbox =
    values.fd_bbox_mode === "user_defined"
      ? [values.fd_bbox_xmin, values.fd_bbox_xmax, values.fd_bbox_ymin,
         values.fd_bbox_ymax, values.fd_bbox_zmin, values.fd_bbox_zmax]
      : null;

  // Build meshing.offset_refinement dict from array
  const offsetRefinementDict: Record<string, object> = {};
  for (const item of values.offset_refinements) {
    if (!item.name) continue;
    offsetRefinementDict[item.name] = {
      level: item.level,
      normal_distance: item.normal_distance,
      parts: splitList(item.parts),
    };
  }
  const customRefinementDict: Record<string, object> = {};
  for (const item of values.custom_refinements) {
    if (!item.name) continue;
    customRefinementDict[item.name] = {
      level: item.level,
      parts: splitList(item.parts),
    };
  }

  // Preserve box_refinement from existing (not editable in form yet)
  const existingMeshing = existingSettings?.setup?.meshing ?? {};

  // Build partial surfaces
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialSurfaces = values.partial_surfaces.map((ps: any) => ({
    name: ps.name,
    output_start_time: ps.output_start_time,
    output_interval: ps.output_interval,
    file_format_ensight: ps.file_format_ensight,
    file_format_h3d: ps.file_format_h3d,
    merge_output: ps.merge_output,
    delete_unmerged: ps.delete_unmerged,
    include_parts: splitList(ps.include_parts),
    exclude_parts: splitList(ps.exclude_parts),
    baffle_export_option: ps.baffle_export_option || null,
    output_variables: ps.output_variables,
  }));

  // Build partial volumes
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialVolumes = values.partial_volumes.map((pv: any) => ({
    name: pv.name,
    output_start_time: pv.output_start_time,
    output_interval: pv.output_interval,
    file_format_ensight: pv.file_format_ensight,
    file_format_h3d: pv.file_format_h3d,
    output_coarsening_active: pv.output_coarsening_active,
    coarsest_target_refinement_level: pv.coarsest_target_refinement_level,
    coarsen_by_num_refinement_levels: pv.coarsen_by_num_refinement_levels,
    merge_output: pv.merge_output,
    delete_unmerged: pv.delete_unmerged,
    bbox_mode: pv.bbox_mode,
    bbox_source_box_name: pv.bbox_mode === "from_meshing_box" ? pv.bbox_source_box_name || null : null,
    bbox_source_parts: pv.bbox_mode === "around_parts" ? splitList(pv.bbox_source_parts) : [],
    bbox: pv.bbox_mode === "user_defined" ? strToBbox(pv.bbox) : null,
    output_variables: pv.output_variables,
  }));

  // Build section cuts
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sectionCuts = values.section_cuts.map((sc: any) => ({
    name: sc.name,
    output_start_time: sc.output_start_time,
    output_interval: sc.output_interval,
    file_format_ensight: sc.file_format_ensight,
    file_format_h3d: sc.file_format_h3d,
    merge_output: sc.merge_output,
    delete_unmerged: sc.delete_unmerged,
    triangulation: sc.triangulation,
    axis_x: sc.axis_x,
    axis_y: sc.axis_y,
    axis_z: sc.axis_z,
    point_x: sc.point_x,
    point_y: sc.point_y,
    point_z: sc.point_z,
    bbox: strToBbox(sc.bbox) ?? [],
    output_variables: sc.output_variables,
  }));

  return {
    setup_option: {
      simulation: {
        temperature_degree: values.temperature_degree,
        simulation_time_with_FP: values.simulation_time_with_FP,
      },
      meshing: {
        triangle_splitting: values.triangle_splitting,
        triangle_splitting_specify_part: values.triangle_splitting_specify_part,
        max_relative_edge_length: values.max_relative_edge_length,
        refinement_level_transition_layers: values.refinement_level_transition_layers,
        domain_bounding_box_relative: values.domain_bounding_box_relative,
        box_offset_relative: values.box_offset_relative,
        box_refinement_porous: values.box_refinement_porous,
      },
      boundary_condition: {
        ground: {
          ground_height_mode: values.ground_height_mode,
          ground_height_absolute: values.ground_height_absolute,
          ground_mode: values.ground_mode,
          overset_wheels: values.overset_wheels,
          ground_patch_active: values.ground_patch_active,
          bl_suction: {
            apply: values.bl_suction_apply,
            no_slip_xmin_pos: values.bl_suction_no_slip_xmin_pos,
            no_slip_xmin_from_belt_xmin: values.bl_suction_from_belt_xmin,
            bl_xmin_offset: values.bl_suction_xmin_offset,
          },
          belt5: {
            wheel_belt_location_auto: values.belt5_wheel_loc_auto,
            narrow_car_fallback: {
              enabled: values.belt5_narrow_fallback,
              min_belt_gap: values.belt5_narrow_min_gap,
            },
            center_belt_position: values.belt5_center_pos,
            center_belt_x_pos: values.belt5_center_x,
            belt_size_wheel: { x: values.belt5_wheel_size_x, y: values.belt5_wheel_size_y },
            belt_size_center: { x: values.belt5_center_size_x, y: values.belt5_center_size_y },
            include_wheel_belt_forces: values.belt5_include_wheel_forces,
          },
          belt1: { belt_size: { x: values.belt1_size_x, y: values.belt1_size_y } },
          apply_static_ground_refinement: values.apply_static_ground_refinement,
        },
        turbulence_generator: {
          enable_ground_tg: values.tg_enable_ground,
          enable_body_tg: values.tg_enable_body,
          ground_tg_num_eddies: values.tg_ground_num_eddies,
          ground_tg_intensity: values.tg_ground_intensity,
          body_tg_num_eddies: values.tg_body_num_eddies,
          body_tg_intensity: values.tg_body_intensity,
        },
      },
      compute: {
        rotate_wheels: values.compute_rotate_wheels,
        porous_media: values.compute_porous_media,
        turbulence_generator: values.compute_turbulence_generator,
        moving_ground: values.compute_moving_ground,
        adjust_ride_height: values.compute_adjust_ride_height,
      },
    },
    simulation_parameter: {
      inflow_velocity: values.inflow_velocity,
      density: values.density,
      dynamic_viscosity: values.dynamic_viscosity,
      temperature: values.temperature,
      specific_gas_constant: values.specific_gas_constant,
      mach_factor: values.mach_factor,
      num_ramp_up_iter: values.num_ramp_up_iter,
      coarsest_voxel_size: values.coarsest_voxel_size,
      number_of_resolution: values.number_of_resolution,
      simulation_time: values.simulation_time,
      simulation_time_FP: values.simulation_time_FP,
      start_averaging_time: values.start_averaging_time,
      avg_window_size: values.avg_window_size,
      yaw_angle: values.yaw_angle,
    },
    setup: {
      domain_bounding_box: [
        values.bbox_xmin, values.bbox_xmax,
        values.bbox_ymin, values.bbox_ymax,
        values.bbox_zmin, values.bbox_zmax,
      ],
      meshing: {
        box_refinement: existingMeshing.box_refinement ?? {},
        part_box_refinement: existingMeshing.part_box_refinement ?? {},
        offset_refinement: offsetRefinementDict,
        custom_refinement: customRefinementDict,
      },
    },
    output: {
      full_data: {
        output_start_time: values.fd_output_start_time,
        output_interval: values.fd_output_interval,
        file_format_ensight: values.fd_format_ensight,
        file_format_h3d: values.fd_format_h3d,
        output_coarsening_active: values.fd_coarsening_active,
        coarsest_target_refinement_level: values.fd_coarsest_target_rl,
        coarsen_by_num_refinement_levels: values.fd_coarsen_by_num_rl,
        merge_output: values.fd_merge_output,
        delete_unmerged: values.fd_delete_unmerged,
        bbox_mode: values.fd_bbox_mode,
        bbox_source_box_name: values.fd_bbox_mode === "from_meshing_box"
          ? values.fd_bbox_source_box || null : null,
        bbox: fdBbox,
        output_variables_full: values.output_variables_full,
        output_variables_surface: values.output_variables_surface,
      },
      partial_surfaces: partialSurfaces,
      partial_volumes: partialVolumes,
      aero_coefficients: {
        reference_area_auto: values.ac_ref_area_auto,
        reference_area: values.ac_ref_area_auto ? null : values.ac_ref_area,
        reference_length_auto: values.ac_ref_length_auto,
        reference_length: values.ac_ref_length_auto ? null : values.ac_ref_length,
        coefficients_along_axis_active: values.ac_along_axis_active,
        num_sections_x: values.ac_num_sections_x,
        num_sections_y: values.ac_num_sections_y,
        num_sections_z: values.ac_num_sections_z,
        export_bounds_active: values.ac_export_bounds_active,
        export_bounds_exclude_domain_parts: values.ac_export_bounds_exclude_domain,
      },
      section_cuts: sectionCuts,
      probes: existingSettings?.output?.probes ?? [],
    },
    target_names: {
      wheel: splitList(values.tn_wheel),
      rim: splitList(values.tn_rim),
      porous: splitList(values.tn_porous),
      car_bounding_box: splitList(values.tn_car_bounding_box),
      baffle: splitList(values.tn_baffle),
      triangle_splitting: splitList(values.tn_triangle_splitting),
      windtunnel: splitList(values.tn_windtunnel),
      wheel_tire_fr_lh: values.tn_wt_fr_lh.trim(),
      wheel_tire_fr_rh: values.tn_wt_fr_rh.trim(),
      wheel_tire_rr_lh: values.tn_wt_rr_lh.trim(),
      wheel_tire_rr_rh: values.tn_wt_rr_rh.trim(),
      overset_fr_lh: values.tn_osm_fr_lh.trim(),
      overset_fr_rh: values.tn_osm_fr_rh.trim(),
      overset_rr_lh: values.tn_osm_rr_lh.trim(),
      overset_rr_rh: values.tn_osm_rr_rh.trim(),
      tire_roughness: values.tn_tire_roughness,
    },
    porous_coefficients: values.porous_coefficients.map((p) => ({
      part_name: p.part_name,
      inertial_resistance: p.inertial_resistance,
      viscous_resistance: p.viscous_resistance,
    })),
  };
}
'''

# ============================================================
# TemplateSettingsForm.tsx
# ============================================================

FORM_CONTENT = r'''/**
 * Shared template settings form fields.
 * Used by both TemplateCreateModal and TemplateVersionCreateModal.
 */
import {
  Accordion,
  ActionIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Divider,
  Group,
  NumberInput,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import type { UseFormReturnType } from "@mantine/form";
import type {
  FormValues,
  OffsetRefinementFormItem,
  CustomRefinementFormItem,
  PartialSurfaceFormItem,
  PartialVolumeFormItem,
  SectionCutFormItem,
  PorousCoeffFormItem,
  OutputVarsFull,
  OutputVarsSurface,
  OutputVarsPartialSurface,
  OutputVarsPartialVolume,
  OutputVarsSectionCut,
} from "../../hooks/useTemplateSettingsForm";

interface Props {
  form: UseFormReturnType<FormValues>;
  simType: string;
}

const isAero = (t: string) => t === "aero" || t === "fan_noise";
const hasWheels = (t: string) => t === "aero";
const hasTG = (t: string) => t === "aero";

// ---- Output Variables Grids --------------------------------------------------

function OvRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <Checkbox
      label={label}
      checked={checked}
      onChange={(e) => onChange(e.currentTarget.checked)}
      size="xs"
    />
  );
}

function OvFullGrid({
  values,
  onChange,
}: {
  values: OutputVarsFull;
  onChange: (next: OutputVarsFull) => void;
}) {
  const set = (k: keyof OutputVarsFull, v: boolean) =>
    onChange({ ...values, [k]: v });
  const keys: (keyof OutputVarsFull)[] = [
    "pressure", "surface_normal", "pressure_std", "pressure_var",
    "time_avg_pressure", "window_avg_pressure", "velocity", "velocity_magnitude",
    "time_avg_velocity", "window_avg_velocity", "wall_shear_stress",
    "time_avg_wall_shear_stress", "window_avg_wall_shear_stress",
    "vorticity", "vorticity_magnitude", "lambda_1", "lambda_2", "lambda_3",
    "q_criterion", "temperature", "time_avg_temperature", "window_avg_temperature",
    "mesh_displacement", "mesh_data",
  ];
  return (
    <SimpleGrid cols={3} spacing="xs">
      {keys.map((k) => (
        <OvRow key={k} label={k} checked={values[k]} onChange={(v) => set(k, v)} />
      ))}
    </SimpleGrid>
  );
}

function OvSurfaceGrid({
  values,
  onChange,
}: {
  values: OutputVarsSurface;
  onChange: (next: OutputVarsSurface) => void;
}) {
  const set = (k: keyof OutputVarsSurface, v: boolean) =>
    onChange({ ...values, [k]: v });
  const keys: (keyof OutputVarsSurface)[] = [
    "pressure", "surface_normal", "pressure_std", "pressure_var",
    "time_avg_pressure", "window_avg_pressure", "velocity", "velocity_magnitude",
    "wall_shear_stress", "time_avg_wall_shear_stress", "window_avg_wall_shear_stress",
    "mesh_displacement", "temperature", "time_avg_temperature", "window_avg_temperature",
  ];
  return (
    <SimpleGrid cols={3} spacing="xs">
      {keys.map((k) => (
        <OvRow key={k} label={k} checked={values[k]} onChange={(v) => set(k, v)} />
      ))}
    </SimpleGrid>
  );
}

function OvPSGrid({
  values,
  onChange,
}: {
  values: OutputVarsPartialSurface;
  onChange: (next: OutputVarsPartialSurface) => void;
}) {
  const set = (k: keyof OutputVarsPartialSurface, v: boolean) =>
    onChange({ ...values, [k]: v });
  const keys: (keyof OutputVarsPartialSurface)[] = [
    "pressure", "pressure_std", "pressure_var", "time_avg_pressure", "window_avg_pressure",
    "velocity", "velocity_magnitude", "wall_shear_stress", "time_avg_wall_shear_stress",
    "window_avg_wall_shear_stress", "surface_normal", "mesh_displacement",
    "temperature", "time_avg_temperature", "window_avg_temperature",
  ];
  return (
    <SimpleGrid cols={3} spacing="xs">
      {keys.map((k) => (
        <OvRow key={k} label={k} checked={values[k]} onChange={(v) => set(k, v)} />
      ))}
    </SimpleGrid>
  );
}

function OvPVGrid({
  values,
  onChange,
}: {
  values: OutputVarsPartialVolume;
  onChange: (next: OutputVarsPartialVolume) => void;
}) {
  const set = (k: keyof OutputVarsPartialVolume, v: boolean) =>
    onChange({ ...values, [k]: v });
  const keys: (keyof OutputVarsPartialVolume)[] = [
    "pressure", "pressure_std", "pressure_var", "time_avg_pressure", "window_avg_pressure",
    "velocity", "velocity_magnitude", "time_avg_velocity", "window_avg_velocity",
    "vorticity", "vorticity_magnitude", "lambda_1", "lambda_2", "lambda_3", "q_criterion",
    "mesh_displacement", "temperature", "time_avg_temperature", "window_avg_temperature",
  ];
  return (
    <SimpleGrid cols={3} spacing="xs">
      {keys.map((k) => (
        <OvRow key={k} label={k} checked={values[k]} onChange={(v) => set(k, v)} />
      ))}
    </SimpleGrid>
  );
}

function OvSCGrid({
  values,
  onChange,
}: {
  values: OutputVarsSectionCut;
  onChange: (next: OutputVarsSectionCut) => void;
}) {
  const set = (k: keyof OutputVarsSectionCut, v: boolean) =>
    onChange({ ...values, [k]: v });
  const keys: (keyof OutputVarsSectionCut)[] = [
    "pressure", "pressure_std", "pressure_var", "time_avg_pressure", "window_avg_pressure",
    "velocity", "velocity_magnitude", "time_avg_velocity", "window_avg_velocity",
    "vorticity", "vorticity_magnitude", "lambda_1", "lambda_2", "lambda_3", "q_criterion",
    "mesh_displacement", "temperature", "time_avg_temperature", "window_avg_temperature",
  ];
  return (
    <SimpleGrid cols={3} spacing="xs">
      {keys.map((k) => (
        <OvRow key={k} label={k} checked={values[k]} onChange={(v) => set(k, v)} />
      ))}
    </SimpleGrid>
  );
}

// ---- Aero body offset defaults -----------------------------------------------

function getBodyOffsetDefaults(
  coarsest: number,
  simType: string
): OffsetRefinementFormItem[] {
  const rl6Dist = coarsest * Math.pow(0.5, 6) * 12;
  const rl7Dist = coarsest * Math.pow(0.5, 7) * 8;
  if (simType === "aero" || simType === "fan_noise") {
    return [
      { name: "Body_Offset_ALL_RL7", level: 7, normal_distance: rl7Dist, parts: "" },
      { name: "Body_Offset_ALL_RL6", level: 6, normal_distance: rl6Dist, parts: "" },
    ];
  }
  // GHN
  return [
    { name: "Body_Offset_ALL_RL6", level: 6, normal_distance: rl6Dist, parts: "" },
  ];
}

// ============================================================
// Main form component
// ============================================================

export function TemplateSettingsForm({ form, simType }: Props) {
  const gm = form.values.ground_mode;
  const isBelt5 = gm === "rotating_belt_5";
  const isBelt1 = gm === "rotating_belt_1";
  const isStatic = gm === "static";
  const isFullMoving = gm === "full_moving";

  // ── Offset refinement helpers ─────────────────────────────────────────
  const addOffsetRefinement = () =>
    form.insertListItem("offset_refinements", {
      name: `Offset_RL6_${form.values.offset_refinements.length + 1}`,
      level: 6,
      normal_distance: form.values.coarsest_voxel_size * Math.pow(0.5, 6) * 12,
      parts: "",
    } as OffsetRefinementFormItem);

  const applyOffsetDefaults = () => {
    const defaults = getBodyOffsetDefaults(form.values.coarsest_voxel_size, simType);
    // Remove existing defaults by name, then prepend
    const existing = form.values.offset_refinements.filter(
      (o) => !defaults.some((d) => d.name === o.name)
    );
    form.setFieldValue("offset_refinements", [...defaults, ...existing]);
  };

  // ── Partial surface helpers ────────────────────────────────────────────
  const addPartialSurface = () =>
    form.insertListItem("partial_surfaces", {
      name: `Partial_Surface_${form.values.partial_surfaces.length + 1}`,
      output_start_time: null,
      output_interval: null,
      file_format_ensight: false,
      file_format_h3d: true,
      merge_output: true,
      delete_unmerged: true,
      include_parts: "",
      exclude_parts: "",
      baffle_export_option: "",
      output_variables: {
        pressure: false, pressure_std: false, pressure_var: false,
        time_avg_pressure: false, window_avg_pressure: false,
        velocity: false, velocity_magnitude: false, wall_shear_stress: false,
        time_avg_wall_shear_stress: false, window_avg_wall_shear_stress: false,
        surface_normal: false, mesh_displacement: false, temperature: false,
        time_avg_temperature: false, window_avg_temperature: false,
      } as OutputVarsPartialSurface,
    } as PartialSurfaceFormItem);

  // ── Partial volume helpers ─────────────────────────────────────────────
  const addPartialVolume = () =>
    form.insertListItem("partial_volumes", {
      name: `Partial_Volume_${form.values.partial_volumes.length + 1}`,
      output_start_time: null,
      output_interval: null,
      file_format_ensight: false,
      file_format_h3d: true,
      output_coarsening_active: false,
      coarsest_target_refinement_level: 3,
      coarsen_by_num_refinement_levels: 0,
      merge_output: true,
      delete_unmerged: true,
      bbox_mode: "user_defined",
      bbox_source_box_name: "",
      bbox_source_parts: "",
      bbox: "",
      output_variables: {
        pressure: false, pressure_std: false, pressure_var: false,
        time_avg_pressure: false, window_avg_pressure: false,
        velocity: false, velocity_magnitude: false,
        time_avg_velocity: false, window_avg_velocity: false,
        mesh_displacement: false, vorticity: false, vorticity_magnitude: false,
        lambda_1: false, lambda_2: false, lambda_3: false, q_criterion: false,
        temperature: false, time_avg_temperature: false, window_avg_temperature: false,
      } as OutputVarsPartialVolume,
    } as PartialVolumeFormItem);

  // ── Section cut helpers ────────────────────────────────────────────────
  const addSectionCut = () =>
    form.insertListItem("section_cuts", {
      name: `Section_Cut_${form.values.section_cuts.length + 1}`,
      output_start_time: null,
      output_interval: null,
      file_format_ensight: false,
      file_format_h3d: true,
      merge_output: true,
      delete_unmerged: true,
      triangulation: false,
      axis_x: 0.0, axis_y: 0.0, axis_z: 1.0,
      point_x: 0.0, point_y: 0.0, point_z: 0.0,
      bbox: "",
      output_variables: {
        pressure: false, pressure_std: false, pressure_var: false,
        time_avg_pressure: false, window_avg_pressure: false,
        velocity: false, velocity_magnitude: false,
        time_avg_velocity: false, window_avg_velocity: false,
        mesh_displacement: false, vorticity: false, vorticity_magnitude: false,
        lambda_1: false, lambda_2: false, lambda_3: false, q_criterion: false,
        temperature: false, time_avg_temperature: false, window_avg_temperature: false,
      } as OutputVarsSectionCut,
    } as SectionCutFormItem);

  return (
    <Accordion multiple defaultValue={["sim", "meshing"]}>
      {/* ── Simulation Run Parameters ──────────────────────────────── */}
      <Accordion.Item value="sim">
        <Accordion.Control>Simulation Run Parameters</Accordion.Control>
        <Accordion.Panel>
          <Stack gap="xs">
            <SimpleGrid cols={2}>
              <NumberInput label="Run time (s)" {...form.getInputProps("simulation_time")} />
              <NumberInput label="Start averaging time (s)" {...form.getInputProps("start_averaging_time")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <NumberInput label="Averaging window size (s)" {...form.getInputProps("avg_window_size")} />
              <NumberInput label="Mach factor" step={0.1} {...form.getInputProps("mach_factor")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <NumberInput label="Ramp-up iterations" {...form.getInputProps("num_ramp_up_iter")} />
              <NumberInput label="Default yaw angle (°)" step={0.5} {...form.getInputProps("yaw_angle")} />
            </SimpleGrid>

            <Divider label="Physical properties" labelPosition="center" />
            <SimpleGrid cols={2}>
              <NumberInput label="Inflow velocity (m/s)" step={0.1} {...form.getInputProps("inflow_velocity")} />
              <NumberInput label="Temperature (°C)" {...form.getInputProps("temperature")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <NumberInput label="Density (kg/m³)" decimalScale={4} step={0.0001} {...form.getInputProps("density")} />
              <NumberInput label="Dynamic viscosity (kg/(s·m))" decimalScale={8} step={1e-7} {...form.getInputProps("dynamic_viscosity")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <NumberInput label="Specific gas constant (J/(kg·K))" {...form.getInputProps("specific_gas_constant")} />
            </SimpleGrid>

            <Divider label="Options" labelPosition="center" />
            <Switch label="Temperature input is °C (auto-convert to K)" {...form.getInputProps("temperature_degree", { type: "checkbox" })} />
            <Switch label="Use flow-passage time instead of fixed run time" {...form.getInputProps("simulation_time_with_FP", { type: "checkbox" })} />
            {form.values.simulation_time_with_FP && (
              <NumberInput label="Flow passages" {...form.getInputProps("simulation_time_FP")} />
            )}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>

      {/* ── Meshing ──────────────────────────────────────────────────── */}
      <Accordion.Item value="meshing">
        <Accordion.Control>Meshing</Accordion.Control>
        <Accordion.Panel>
          <Stack gap="xs">
            <SimpleGrid cols={2}>
              <NumberInput
                label="Coarsest voxel size (m)"
                description={`Finest ≈ ${(form.values.coarsest_voxel_size / Math.pow(2, form.values.number_of_resolution)).toExponential(4)} m`}
                decimalScale={4}
                step={0.001}
                {...form.getInputProps("coarsest_voxel_size")}
              />
              <NumberInput label="Number of refinement levels" {...form.getInputProps("number_of_resolution")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <NumberInput label="Refinement level transition layers" {...form.getInputProps("refinement_level_transition_layers")} />
              <NumberInput label="Max relative edge length" step={0.5} {...form.getInputProps("max_relative_edge_length")} />
            </SimpleGrid>

            <Switch label="Triangle splitting" {...form.getInputProps("triangle_splitting", { type: "checkbox" })} />
            {form.values.triangle_splitting && (
              <>
                <Switch label="Apply triangle splitting to specified parts only" {...form.getInputProps("triangle_splitting_specify_part", { type: "checkbox" })} />
                {form.values.triangle_splitting_specify_part && (
                  <TextInput label="Triangle splitting part patterns (comma-separated)" placeholder="Part_A, Part_B" {...form.getInputProps("tn_triangle_splitting")} />
                )}
              </>
            )}

            <Switch label="Domain bounding box defined relative to car size" {...form.getInputProps("domain_bounding_box_relative", { type: "checkbox" })} />
            <Switch label="Box/offset refinement relative to car size" {...form.getInputProps("box_offset_relative", { type: "checkbox" })} />
            <Switch label="Add box refinement for porous media" {...form.getInputProps("box_refinement_porous", { type: "checkbox" })} />

            <Divider label="Domain bounding box multipliers" labelPosition="center" />
            <SimpleGrid cols={3}>
              <NumberInput label="X min mult" step={0.5} {...form.getInputProps("bbox_xmin")} />
              <NumberInput label="X max mult" step={0.5} {...form.getInputProps("bbox_xmax")} />
              <NumberInput label="Y min mult" step={0.5} {...form.getInputProps("bbox_ymin")} />
            </SimpleGrid>
            <SimpleGrid cols={3}>
              <NumberInput label="Y max mult" step={0.5} {...form.getInputProps("bbox_ymax")} />
              <NumberInput label="Z min mult" step={0.5} {...form.getInputProps("bbox_zmin")} />
              <NumberInput label="Z max mult" step={0.5} {...form.getInputProps("bbox_zmax")} />
            </SimpleGrid>

            {/* Offset refinement dynamic list */}
            <Divider label="Offset Refinement" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Offset refinement zones ({form.values.offset_refinements.length})</Text>
              <Group gap="xs">
                <Button size="xs" variant="light" onClick={applyOffsetDefaults}>
                  Apply body defaults
                </Button>
                <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addOffsetRefinement}>
                  Add
                </Button>
              </Group>
            </Group>
            {form.values.offset_refinements.map((item, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={4}>
                  <Badge size="sm" variant="outline">Offset {idx + 1}</Badge>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("offset_refinements", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <SimpleGrid cols={2}>
                  <TextInput label="Name" {...form.getInputProps(`offset_refinements.${idx}.name`)} />
                  <NumberInput label="Refinement level" {...form.getInputProps(`offset_refinements.${idx}.level`)} />
                </SimpleGrid>
                <NumberInput label="Normal distance (m)" decimalScale={5} step={0.001} {...form.getInputProps(`offset_refinements.${idx}.normal_distance`)} />
                <TextInput label="Parts (comma-separated; empty = body offset)" placeholder="Leave empty for body offset, or specify part patterns" {...form.getInputProps(`offset_refinements.${idx}.parts`)} />
              </Paper>
            ))}

            {/* Custom refinement dynamic list */}
            <Divider label="Custom Refinement" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Custom refinement zones ({form.values.custom_refinements.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />}
                onClick={() => form.insertListItem("custom_refinements", {
                  name: `Custom_RL7_${form.values.custom_refinements.length + 1}`,
                  level: 7, parts: "",
                } as CustomRefinementFormItem)}>
                Add
              </Button>
            </Group>
            {form.values.custom_refinements.map((_, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={4}>
                  <Badge size="sm" variant="outline">Custom {idx + 1}</Badge>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("custom_refinements", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <SimpleGrid cols={2}>
                  <TextInput label="Name" {...form.getInputProps(`custom_refinements.${idx}.name`)} />
                  <NumberInput label="Refinement level" {...form.getInputProps(`custom_refinements.${idx}.level`)} />
                </SimpleGrid>
                <TextInput label="Parts (comma-separated)" placeholder="Part_A, Part_B" {...form.getInputProps(`custom_refinements.${idx}.parts`)} />
              </Paper>
            ))}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>

      {/* ── Boundary Conditions ───────────────────────────────────────── */}
      <Accordion.Item value="bc">
        <Accordion.Control>Boundary Conditions</Accordion.Control>
        <Accordion.Panel>
          <Stack gap="sm">
            {/* Ground height */}
            <Select
              label="Ground height definition"
              data={[
                { value: "from_geometry", label: "From geometry (z_min of STL)" },
                { value: "absolute", label: "Absolute z-position" },
              ]}
              {...form.getInputProps("ground_height_mode")}
            />
            {form.values.ground_height_mode === "absolute" && (
              <NumberInput label="Ground height, absolute z (m)" step={0.01} {...form.getInputProps("ground_height_absolute")} />
            )}

            <Switch label="Ground patch active" {...form.getInputProps("ground_patch_active", { type: "checkbox" })} />

            {/* Ground mode — aero only */}
            {isAero(simType) && (
              <>
                <Select
                  label="Ground condition"
                  data={[
                    { value: "rotating_belt_5", label: "5-belt rotating" },
                    { value: "rotating_belt_1", label: "1-belt rotating" },
                    { value: "full_moving", label: "Full moving ground" },
                    { value: "static", label: "Static ground" },
                  ]}
                  {...form.getInputProps("ground_mode")}
                />

                {!isFullMoving && (
                  <Switch label="Overset mesh for rotating wheels (OSM)" {...form.getInputProps("overset_wheels", { type: "checkbox" })} />
                )}

                {!isFullMoving && (
                  <>
                    <Switch label="Apply BL suction (no-slip / slip ground split)" {...form.getInputProps("bl_suction_apply", { type: "checkbox" })} />
                    {form.values.bl_suction_apply && (
                      <>
                        {isBelt5 ? (
                          <>
                            <Switch label="Derive no-slip x-min from center belt x-min" {...form.getInputProps("bl_suction_from_belt_xmin", { type: "checkbox" })} />
                            {!form.values.bl_suction_from_belt_xmin && (
                              <NumberInput label="No-slip x-min position (m)" step={0.01} {...form.getInputProps("bl_suction_no_slip_xmin_pos")} />
                            )}
                            <NumberInput label="BL x-min offset from belt (m)" step={0.01} allowDecimal {...form.getInputProps("bl_suction_xmin_offset")} />
                          </>
                        ) : (
                          <NumberInput label="No-slip x-min position (m)" step={0.01} {...form.getInputProps("bl_suction_no_slip_xmin_pos")} />
                        )}
                      </>
                    )}
                  </>
                )}

                {isStatic && (
                  <Switch label="Apply box refinement for static ground" {...form.getInputProps("apply_static_ground_refinement", { type: "checkbox" })} />
                )}

                {isBelt5 && (
                  <>
                    <Divider label="5-Belt Configuration" labelPosition="center" />
                    <Switch label="Wheel belt position auto (from tire centroid)" {...form.getInputProps("belt5_wheel_loc_auto", { type: "checkbox" })} />
                    <Switch label="Narrow car fallback (minimum belt gap)" {...form.getInputProps("belt5_narrow_fallback", { type: "checkbox" })} />
                    {form.values.belt5_narrow_fallback && (
                      <NumberInput label="Minimum belt gap (m)" step={0.05} {...form.getInputProps("belt5_narrow_min_gap")} />
                    )}
                    <Select
                      label="Center belt position"
                      data={[
                        { value: "at_wheelbase_center", label: "At wheelbase center" },
                        { value: "user_specified", label: "User specified" },
                      ]}
                      {...form.getInputProps("belt5_center_pos")}
                    />
                    {form.values.belt5_center_pos === "user_specified" && (
                      <NumberInput label="Center belt x position (m)" step={0.01} {...form.getInputProps("belt5_center_x")} />
                    )}
                    <Text size="sm" fw={500}>Wheel belt size (m)</Text>
                    <SimpleGrid cols={2}>
                      <NumberInput label="Width (x)" step={0.05} {...form.getInputProps("belt5_wheel_size_x")} />
                      <NumberInput label="Length (y)" step={0.05} {...form.getInputProps("belt5_wheel_size_y")} />
                    </SimpleGrid>
                    <Text size="sm" fw={500}>Center belt size (m)</Text>
                    <SimpleGrid cols={2}>
                      <NumberInput label="Width (x)" step={0.05} {...form.getInputProps("belt5_center_size_x")} />
                      <NumberInput label="Length (y)" step={0.05} {...form.getInputProps("belt5_center_size_y")} />
                    </SimpleGrid>
                    <Switch label="Include wheel belt forces in aerodynamic loads" {...form.getInputProps("belt5_include_wheel_forces", { type: "checkbox" })} />
                  </>
                )}

                {isBelt1 && (
                  <>
                    <Divider label="1-Belt Configuration" labelPosition="center" />
                    <Text size="sm" fw={500}>Belt size (m)</Text>
                    <SimpleGrid cols={2}>
                      <NumberInput label="Width (x)" step={0.05} {...form.getInputProps("belt1_size_x")} />
                      <NumberInput label="Length (y)" step={0.1} {...form.getInputProps("belt1_size_y")} />
                    </SimpleGrid>
                  </>
                )}
              </>
            )}

            {/* GHN/fan_noise BL suction (simple, no belt options) */}
            {!isAero(simType) && (
              <>
                <Switch label="Apply BL suction (no-slip / slip ground split)" {...form.getInputProps("bl_suction_apply", { type: "checkbox" })} />
                {form.values.bl_suction_apply && (
                  <NumberInput label="No-slip x-min position (m)" step={0.01} {...form.getInputProps("bl_suction_no_slip_xmin_pos")} />
                )}
              </>
            )}

            {/* Turbulence generator — aero only */}
            {hasTG(simType) && (
              <>
                <Divider label="Turbulence Generator" labelPosition="center" />
                <SimpleGrid cols={2}>
                  <Switch label="Enable ground TG" {...form.getInputProps("tg_enable_ground", { type: "checkbox" })} />
                  <Switch label="Enable body TG" {...form.getInputProps("tg_enable_body", { type: "checkbox" })} />
                </SimpleGrid>
                {form.values.tg_enable_ground && (
                  <SimpleGrid cols={2}>
                    <NumberInput label="Ground TG num eddies" {...form.getInputProps("tg_ground_num_eddies")} />
                    <NumberInput label="Ground TG intensity" decimalScale={3} step={0.005} {...form.getInputProps("tg_ground_intensity")} />
                  </SimpleGrid>
                )}
                {form.values.tg_enable_body && (
                  <SimpleGrid cols={2}>
                    <NumberInput label="Body TG num eddies" {...form.getInputProps("tg_body_num_eddies")} />
                    <NumberInput label="Body TG intensity" decimalScale={3} step={0.005} {...form.getInputProps("tg_body_intensity")} />
                  </SimpleGrid>
                )}
              </>
            )}

            {/* Compute options */}
            <Divider label="Compute options (defaults)" labelPosition="center" />
            <Switch label="Rotate wheels (OSM + rotating wall BC)" {...form.getInputProps("compute_rotate_wheels", { type: "checkbox" })} />
            <Switch label="Porous media" {...form.getInputProps("compute_porous_media", { type: "checkbox" })} />
            {hasTG(simType) && (
              <Switch
                label="Turbulence generator"
                disabled={!form.values.tg_enable_ground && !form.values.tg_enable_body}
                {...form.getInputProps("compute_turbulence_generator", { type: "checkbox" })}
              />
            )}
            <Switch
              label="Moving ground (belt BC)"
              disabled={!form.values.compute_rotate_wheels}
              {...form.getInputProps("compute_moving_ground", { type: "checkbox" })}
            />
            <Switch label="Adjust ride height" {...form.getInputProps("compute_adjust_ride_height", { type: "checkbox" })} />

            {/* Porous media coefficients at template level */}
            <Divider label="Porous Media Coefficients (template defaults)" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Porous parts ({form.values.porous_coefficients.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />}
                onClick={() => form.insertListItem("porous_coefficients", {
                  part_name: "", inertial_resistance: 0.0, viscous_resistance: 0.0,
                } as PorousCoeffFormItem)}>
                Add porous part
              </Button>
            </Group>
            <Text size="xs" c="dimmed">
              These serve as defaults. Can be overridden per Configuration.
            </Text>
            {form.values.porous_coefficients.map((_, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={4}>
                  <Badge size="sm" variant="outline">Porous {idx + 1}</Badge>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("porous_coefficients", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <TextInput label="Part name (must match STL part name exactly)" {...form.getInputProps(`porous_coefficients.${idx}.part_name`)} />
                <SimpleGrid cols={2}>
                  <NumberInput label="Inertial resistance (1/m)" decimalScale={2} step={1} {...form.getInputProps(`porous_coefficients.${idx}.inertial_resistance`)} />
                  <NumberInput label="Viscous resistance (1/s)" decimalScale={2} step={1} {...form.getInputProps(`porous_coefficients.${idx}.viscous_resistance`)} />
                </SimpleGrid>
              </Paper>
            ))}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>

      {/* ── Output ───────────────────────────────────────────────────── */}
      <Accordion.Item value="output">
        <Accordion.Control>Output</Accordion.Control>
        <Accordion.Panel>
          <Stack gap="sm">
            {/* Full data */}
            <Divider label="Full data output" labelPosition="center" />
            <SimpleGrid cols={2}>
              <NumberInput label="Output start time (s, blank=auto)" allowDecimal step={0.1} {...form.getInputProps("fd_output_start_time")} />
              <NumberInput label="Output interval (s, blank=auto)" allowDecimal step={0.1} {...form.getInputProps("fd_output_interval")} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <Switch label="Format: EnSight" {...form.getInputProps("fd_format_ensight", { type: "checkbox" })} />
              <Switch label="Format: H3D" {...form.getInputProps("fd_format_h3d", { type: "checkbox" })} />
            </SimpleGrid>
            <SimpleGrid cols={2}>
              <Switch label="Merge output files" {...form.getInputProps("fd_merge_output", { type: "checkbox" })} />
              <Switch label="Delete unmerged files" disabled={!form.values.fd_merge_output} {...form.getInputProps("fd_delete_unmerged", { type: "checkbox" })} />
            </SimpleGrid>
            <Switch label="Output coarsening" {...form.getInputProps("fd_coarsening_active", { type: "checkbox" })} />
            {form.values.fd_coarsening_active && (
              <SimpleGrid cols={2}>
                <NumberInput label="Coarsest target RL" {...form.getInputProps("fd_coarsest_target_rl")} />
                <NumberInput label="Coarsen by num RL" {...form.getInputProps("fd_coarsen_by_num_rl")} />
              </SimpleGrid>
            )}
            <Select
              label="Output bounding box"
              data={[
                { value: "from_meshing_box", label: "From meshing box" },
                { value: "user_defined", label: "User defined" },
              ]}
              {...form.getInputProps("fd_bbox_mode")}
            />
            {form.values.fd_bbox_mode === "from_meshing_box" && (
              <TextInput label="Source box name" placeholder="e.g. Box_RL1" {...form.getInputProps("fd_bbox_source_box")} />
            )}
            {form.values.fd_bbox_mode === "user_defined" && (
              <>
                <SimpleGrid cols={3}>
                  <NumberInput label="X min (m)" step={0.5} {...form.getInputProps("fd_bbox_xmin")} />
                  <NumberInput label="X max (m)" step={0.5} {...form.getInputProps("fd_bbox_xmax")} />
                  <NumberInput label="Y min (m)" step={0.5} {...form.getInputProps("fd_bbox_ymin")} />
                </SimpleGrid>
                <SimpleGrid cols={3}>
                  <NumberInput label="Y max (m)" step={0.5} {...form.getInputProps("fd_bbox_ymax")} />
                  <NumberInput label="Z min (m)" step={0.5} {...form.getInputProps("fd_bbox_zmin")} />
                  <NumberInput label="Z max (m)" step={0.5} {...form.getInputProps("fd_bbox_zmax")} />
                </SimpleGrid>
              </>
            )}

            {/* Output variables */}
            <Divider label="Output variables — Volume" labelPosition="center" />
            <OvFullGrid
              values={form.values.output_variables_full}
              onChange={(v) => form.setFieldValue("output_variables_full", v)}
            />
            <Divider label="Output variables — Surface" labelPosition="center" />
            <OvSurfaceGrid
              values={form.values.output_variables_surface}
              onChange={(v) => form.setFieldValue("output_variables_surface", v)}
            />

            {/* Aero coefficients */}
            {isAero(simType) && (
              <>
                <Divider label="Aero coefficients" labelPosition="center" />
                <Switch label="Reference area: auto (Ultrafluid calculates)" {...form.getInputProps("ac_ref_area_auto", { type: "checkbox" })} />
                {!form.values.ac_ref_area_auto && (
                  <NumberInput label="Reference area (m²)" decimalScale={4} step={0.1} {...form.getInputProps("ac_ref_area")} />
                )}
                <Switch label="Reference length: auto (wheelbase from wheel centers)" {...form.getInputProps("ac_ref_length_auto", { type: "checkbox" })} />
                {!form.values.ac_ref_length_auto && (
                  <NumberInput label="Reference length (m)" decimalScale={4} step={0.1} {...form.getInputProps("ac_ref_length")} />
                )}
                <Switch label="Coefficients along axis" {...form.getInputProps("ac_along_axis_active", { type: "checkbox" })} />
                {form.values.ac_along_axis_active && (
                  <>
                    <SimpleGrid cols={3}>
                      <NumberInput label="Sections X" {...form.getInputProps("ac_num_sections_x")} />
                      <NumberInput label="Sections Y" {...form.getInputProps("ac_num_sections_y")} />
                      <NumberInput label="Sections Z" {...form.getInputProps("ac_num_sections_z")} />
                    </SimpleGrid>
                    <SimpleGrid cols={2}>
                      <Switch label="Export bounds active" {...form.getInputProps("ac_export_bounds_active", { type: "checkbox" })} />
                      <Switch label="Exclude domain parts from bounds" {...form.getInputProps("ac_export_bounds_exclude_domain", { type: "checkbox" })} />
                    </SimpleGrid>
                  </>
                )}
              </>
            )}

            {/* Partial Surfaces */}
            <Divider label="Partial Surfaces" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Partial surface outputs ({form.values.partial_surfaces.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addPartialSurface}>Add</Button>
            </Group>
            {form.values.partial_surfaces.map((ps, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={6}>
                  <Title order={6}>{ps.name || `Partial Surface ${idx + 1}`}</Title>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("partial_surfaces", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <Stack gap="xs">
                  <TextInput label="Name" {...form.getInputProps(`partial_surfaces.${idx}.name`)} />
                  <SimpleGrid cols={2}>
                    <NumberInput label="Output start time (s, blank=auto)" {...form.getInputProps(`partial_surfaces.${idx}.output_start_time`)} />
                    <NumberInput label="Output interval (s, blank=auto)" {...form.getInputProps(`partial_surfaces.${idx}.output_interval`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Format: EnSight" {...form.getInputProps(`partial_surfaces.${idx}.file_format_ensight`, { type: "checkbox" })} />
                    <Switch label="Format: H3D" {...form.getInputProps(`partial_surfaces.${idx}.file_format_h3d`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Merge output" {...form.getInputProps(`partial_surfaces.${idx}.merge_output`, { type: "checkbox" })} />
                    <Switch label="Delete unmerged" {...form.getInputProps(`partial_surfaces.${idx}.delete_unmerged`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <TextInput label="Include parts (comma-separated; empty = all)" {...form.getInputProps(`partial_surfaces.${idx}.include_parts`)} />
                  <TextInput label="Exclude parts (comma-separated)" {...form.getInputProps(`partial_surfaces.${idx}.exclude_parts`)} />
                  <Select
                    label="Baffle exclude option"
                    clearable
                    data={[
                      { value: "front_only", label: "Front only" },
                      { value: "back_only", label: "Back only" },
                      { value: "both", label: "Both" },
                    ]}
                    {...form.getInputProps(`partial_surfaces.${idx}.baffle_export_option`)}
                  />
                  <Divider label="Output variables" labelPosition="center" />
                  <OvPSGrid
                    values={ps.output_variables}
                    onChange={(v) => form.setFieldValue(`partial_surfaces.${idx}.output_variables`, v)}
                  />
                </Stack>
              </Paper>
            ))}

            {/* Partial Volumes */}
            <Divider label="Partial Volumes" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Partial volume outputs ({form.values.partial_volumes.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addPartialVolume}>Add</Button>
            </Group>
            {form.values.partial_volumes.map((pv, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={6}>
                  <Title order={6}>{pv.name || `Partial Volume ${idx + 1}`}</Title>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("partial_volumes", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <Stack gap="xs">
                  <TextInput label="Name" {...form.getInputProps(`partial_volumes.${idx}.name`)} />
                  <SimpleGrid cols={2}>
                    <NumberInput label="Output start time (s, blank=auto)" {...form.getInputProps(`partial_volumes.${idx}.output_start_time`)} />
                    <NumberInput label="Output interval (s, blank=auto)" {...form.getInputProps(`partial_volumes.${idx}.output_interval`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Format: EnSight" {...form.getInputProps(`partial_volumes.${idx}.file_format_ensight`, { type: "checkbox" })} />
                    <Switch label="Format: H3D" {...form.getInputProps(`partial_volumes.${idx}.file_format_h3d`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <Switch label="Output coarsening" {...form.getInputProps(`partial_volumes.${idx}.output_coarsening_active`, { type: "checkbox" })} />
                  {pv.output_coarsening_active && (
                    <SimpleGrid cols={2}>
                      <NumberInput label="Coarsest target RL" {...form.getInputProps(`partial_volumes.${idx}.coarsest_target_refinement_level`)} />
                      <NumberInput label="Coarsen by num RL" {...form.getInputProps(`partial_volumes.${idx}.coarsen_by_num_refinement_levels`)} />
                    </SimpleGrid>
                  )}
                  <SimpleGrid cols={2}>
                    <Switch label="Merge output" {...form.getInputProps(`partial_volumes.${idx}.merge_output`, { type: "checkbox" })} />
                    <Switch label="Delete unmerged" {...form.getInputProps(`partial_volumes.${idx}.delete_unmerged`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <Select
                    label="Bounding box mode"
                    data={[
                      { value: "from_meshing_box", label: "From meshing box" },
                      { value: "around_parts", label: "Around specified parts" },
                      { value: "user_defined", label: "User defined" },
                    ]}
                    {...form.getInputProps(`partial_volumes.${idx}.bbox_mode`)}
                  />
                  {pv.bbox_mode === "from_meshing_box" && (
                    <TextInput label="Source box name" placeholder="e.g. Box_RL1" {...form.getInputProps(`partial_volumes.${idx}.bbox_source_box_name`)} />
                  )}
                  {pv.bbox_mode === "around_parts" && (
                    <TextInput label="Parts for bbox computation (comma-separated)" {...form.getInputProps(`partial_volumes.${idx}.bbox_source_parts`)} />
                  )}
                  {pv.bbox_mode === "user_defined" && (
                    <TextInput label="Bounding box (xmin,xmax,ymin,ymax,zmin,zmax)" placeholder="-5,15,-12,12,0,8" {...form.getInputProps(`partial_volumes.${idx}.bbox`)} />
                  )}
                  <Divider label="Output variables" labelPosition="center" />
                  <OvPVGrid
                    values={pv.output_variables}
                    onChange={(v) => form.setFieldValue(`partial_volumes.${idx}.output_variables`, v)}
                  />
                </Stack>
              </Paper>
            ))}

            {/* Section Cuts */}
            <Divider label="Section Cuts" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Section cut outputs ({form.values.section_cuts.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addSectionCut}>Add</Button>
            </Group>
            {form.values.section_cuts.map((sc, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={6}>
                  <Title order={6}>{sc.name || `Section Cut ${idx + 1}`}</Title>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("section_cuts", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <Stack gap="xs">
                  <TextInput label="Name" {...form.getInputProps(`section_cuts.${idx}.name`)} />
                  <SimpleGrid cols={2}>
                    <NumberInput label="Output start time (s, blank=auto)" {...form.getInputProps(`section_cuts.${idx}.output_start_time`)} />
                    <NumberInput label="Output interval (s, blank=auto)" {...form.getInputProps(`section_cuts.${idx}.output_interval`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Format: EnSight" {...form.getInputProps(`section_cuts.${idx}.file_format_ensight`, { type: "checkbox" })} />
                    <Switch label="Format: H3D" {...form.getInputProps(`section_cuts.${idx}.file_format_h3d`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Merge output" {...form.getInputProps(`section_cuts.${idx}.merge_output`, { type: "checkbox" })} />
                    <Switch label="Triangulation" {...form.getInputProps(`section_cuts.${idx}.triangulation`, { type: "checkbox" })} />
                  </SimpleGrid>
                  <Divider label="Cut plane definition" labelPosition="center" />
                  <Text size="xs" c="dimmed">Axis = normal direction of cut plane (unit vector)</Text>
                  <SimpleGrid cols={3}>
                    <NumberInput label="Axis X" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.axis_x`)} />
                    <NumberInput label="Axis Y" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.axis_y`)} />
                    <NumberInput label="Axis Z" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.axis_z`)} />
                  </SimpleGrid>
                  <Text size="xs" c="dimmed">Point on the cut plane</Text>
                  <SimpleGrid cols={3}>
                    <NumberInput label="Point X (m)" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.point_x`)} />
                    <NumberInput label="Point Y (m)" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.point_y`)} />
                    <NumberInput label="Point Z (m)" decimalScale={3} step={0.1} {...form.getInputProps(`section_cuts.${idx}.point_z`)} />
                  </SimpleGrid>
                  <TextInput label="Bounding box (xmin,xmax,ymin,ymax,zmin,zmax; blank = full domain)" placeholder="-5,15,-12,12,0,8" {...form.getInputProps(`section_cuts.${idx}.bbox`)} />
                  <Divider label="Output variables" labelPosition="center" />
                  <OvSCGrid
                    values={sc.output_variables}
                    onChange={(v) => form.setFieldValue(`section_cuts.${idx}.output_variables`, v)}
                  />
                </Stack>
              </Paper>
            ))}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>

      {/* ── Target Part Names ─────────────────────────────────────────── */}
      <Accordion.Item value="targets">
        <Accordion.Control>Target Part Names</Accordion.Control>
        <Accordion.Panel>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Use comma-separated substrings/prefixes that match part names in the STL.
            </Text>
            <TextInput label="Wheel parts" placeholder="Wheel_" {...form.getInputProps("tn_wheel")} />
            {hasWheels(simType) && (
              <>
                <TextInput label="Rim parts (for wheel axis detection)" placeholder="_Spokes_" {...form.getInputProps("tn_rim")} />
                <Divider label="Individual tire parts (for belt auto-position & roughness)" labelPosition="center" />
                <SimpleGrid cols={2}>
                  <TextInput label="FR LH tire" placeholder="WheelTire_FR_LH" {...form.getInputProps("tn_wt_fr_lh")} />
                  <TextInput label="FR RH tire" placeholder="WheelTire_FR_RH" {...form.getInputProps("tn_wt_fr_rh")} />
                  <TextInput label="RR LH tire" placeholder="WheelTire_RR_LH" {...form.getInputProps("tn_wt_rr_lh")} />
                  <TextInput label="RR RH tire" placeholder="WheelTire_RR_RH" {...form.getInputProps("tn_wt_rr_rh")} />
                </SimpleGrid>
                <NumberInput label="Tire roughness (m)" decimalScale={5} step={0.0001} {...form.getInputProps("tn_tire_roughness")} />
                {form.values.overset_wheels && (
                  <>
                    <Divider label="OSM region parts" labelPosition="center" />
                    <SimpleGrid cols={2}>
                      <TextInput label="FR LH OSM" placeholder="Overset_FR_LH" {...form.getInputProps("tn_osm_fr_lh")} />
                      <TextInput label="FR RH OSM" placeholder="Overset_FR_RH" {...form.getInputProps("tn_osm_fr_rh")} />
                      <TextInput label="RR LH OSM" placeholder="Overset_RR_LH" {...form.getInputProps("tn_osm_rr_lh")} />
                      <TextInput label="RR RH OSM" placeholder="Overset_RR_RH" {...form.getInputProps("tn_osm_rr_rh")} />
                    </SimpleGrid>
                  </>
                )}
              </>
            )}
            <TextInput label="Porous media parts" placeholder="Porous_Media_" {...form.getInputProps("tn_porous")} />
            <TextInput label="Baffle parts" placeholder="_Baffle_" {...form.getInputProps("tn_baffle")} />
            <TextInput label="Car bounding box parts" placeholder="Body_" {...form.getInputProps("tn_car_bounding_box")} />
            <TextInput label="Wind tunnel parts (excluded from forces + offset refinement)" placeholder="WindTunnel_" {...form.getInputProps("tn_windtunnel")} />
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
'''

HOOKS.write_text(HOOK_CONTENT, encoding="utf-8")
FORM.write_text(FORM_CONTENT, encoding="utf-8")

print(f"Done. Written to:\n  {HOOKS}\n  {FORM}")
