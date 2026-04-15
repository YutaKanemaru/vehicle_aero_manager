/**
 * Shared form logic for Template create / version create modals.
 */

import { templateDefaults as D } from "../api/templateDefaults";

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
  output_start_time: number;
  output_interval: number;
  file_format: string;
  merge_output: boolean;
  delete_unmerged: boolean;
  include_parts: string;           // comma-separated
  exclude_parts: string;           // comma-separated
  baffle_export_option: "front_only" | "back_only" | "both" | "";
  output_variables: OutputVarsPartialSurface;
}

export interface PartialVolumeFormItem {
  name: string;
  output_start_time: number;
  output_interval: number;
  file_format: string;
  output_coarsening_active: boolean;
  coarsest_target_refinement_level: number;
  coarsen_by_num_refinement_levels: number;
  merge_output: boolean;
  delete_unmerged: boolean;
  bbox_mode: "from_meshing_box" | "around_parts" | "user_defined";
  bbox_source_box_name: string;
  bbox_source_parts: string;       // comma-separated
  bbox_offset_xmin: number;        // m — offset from parts bbox in -X (around_parts only)
  bbox_offset_xmax: number;        // m — offset from parts bbox in +X
  bbox_offset_ymin: number;        // m — offset from parts bbox in -Y
  bbox_offset_ymax: number;        // m — offset from parts bbox in +Y
  bbox_offset_zmin: number;        // m — offset from parts bbox in -Z
  bbox_offset_zmax: number;        // m — offset from parts bbox in +Z
  bbox: string;                    // "xmin,xmax,ymin,ymax,zmin,zmax" (user_defined only)
  output_variables: OutputVarsPartialVolume;
}

export interface SectionCutFormItem {
  name: string;
  output_start_time: number;
  output_interval: number;
  file_format: string;
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

export interface ProbePointFormItem {
  x_pos: number;
  y_pos: number;
  z_pos: number;
  description: string;
}

export interface ProbeFileOutputVars {
  pressure: boolean | null;
  time_avg_pressure: boolean | null;
  window_avg_pressure: boolean | null;
  cp: boolean | null;
  velocity: boolean | null;
  time_avg_velocity: boolean | null;
  window_avg_velocity: boolean | null;
  velocity_magnitude: boolean | null;
  time_avg_velocity_magnitude: boolean | null;
  window_avg_velocity_magnitude: boolean | null;
  wall_shear_stress: boolean | null;
  time_avg_wall_shear_stress: boolean | null;
  window_avg_wall_shear_stress: boolean | null;
  density: boolean | null;
  time_avg_density: boolean | null;
  window_avg_density: boolean | null;
  pressure_std: boolean | null;
  pressure_var: boolean | null;
}

export interface ProbeFileFormItem {
  name: string;
  probe_type: string;          // "volume" | "surface"
  radius: number;
  output_frequency: number;
  output_start_iteration: number;
  scientific_notation: boolean;
  output_precision: number;
  output_variables: ProbeFileOutputVars;
  points: ProbePointFormItem[];
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

export interface BoxRefinementFormItem {
  name: string;
  level: number;
  box_type: "vehicle_bbox_factors" | "around_parts" | "user_defined";
  // ─── vehicle_bbox_factors / user_defined modes ───────────────────
  box_xmin: number;
  box_xmax: number;
  box_ymin: number;
  box_ymax: number;
  box_zmin: number;
  box_zmax: number;
  // ─── around_parts mode ───────────────────────────────────────────
  parts: string;               // comma-separated part name patterns
  offset_xmin: number;         // m — extend beyond parts bbox in -X
  offset_xmax: number;         // m — extend beyond parts bbox in +X
  offset_ymin: number;         // m — extend beyond parts bbox in -Y
  offset_ymax: number;         // m — extend beyond parts bbox in +Y
  offset_zmin: number;         // m — extend beyond parts bbox in -Z
  offset_zmax: number;         // m — extend beyond parts bbox in +Z
}

export interface PorousCoeffFormItem {
  part_name: string;
  inertial_resistance: number;
  viscous_resistance: number;
}

export interface TriangleSplittingInstanceFormItem {
  name: string;
  active: boolean;
  max_absolute_edge_length: number;
  max_relative_edge_length: number;
  parts: string; // comma-separated
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
  // ── Simulation parameters — sourced from D.simulation_parameter ───────
  inflow_velocity: D.simulation_parameter.inflow_velocity,
  density: D.simulation_parameter.density,
  dynamic_viscosity: D.simulation_parameter.dynamic_viscosity,
  temperature: D.simulation_parameter.temperature,
  specific_gas_constant: D.simulation_parameter.specific_gas_constant,
  mach_factor: D.simulation_parameter.mach_factor,
  num_ramp_up_iter: D.simulation_parameter.num_ramp_up_iter,
  coarsest_voxel_size: D.simulation_parameter.coarsest_voxel_size,
  number_of_resolution: D.simulation_parameter.number_of_resolution,
  simulation_time: D.simulation_parameter.simulation_time,
  simulation_time_FP: D.simulation_parameter.simulation_time_FP,
  start_averaging_time: D.simulation_parameter.start_averaging_time,
  avg_window_size: D.simulation_parameter.avg_window_size,
  yaw_angle: D.simulation_parameter.yaw_angle,
  temperature_degree: D.setup_option.simulation.temperature_degree,
  simulation_time_with_FP: D.setup_option.simulation.simulation_time_with_FP,

  // ── Meshing — sourced from D.setup_option.meshing ──────────────────────
  triangle_splitting: D.setup_option.meshing.triangle_splitting,
  ts_max_absolute_edge_length: D.setup_option.meshing.max_absolute_edge_length as number,
  max_relative_edge_length: D.setup_option.meshing.max_relative_edge_length,
  triangle_splitting_instances: [] as TriangleSplittingInstanceFormItem[],
  refinement_level_transition_layers: D.setup_option.meshing.refinement_level_transition_layers,
  box_refinement_porous: D.setup_option.meshing.box_refinement_porous,
  // Domain bounding box multipliers — sourced from D.setup.domain_bounding_box
  bbox_xmin: D.setup.domain_bounding_box[0] as number,
  bbox_xmax: D.setup.domain_bounding_box[1] as number,
  bbox_ymin: D.setup.domain_bounding_box[2] as number,
  bbox_ymax: D.setup.domain_bounding_box[3] as number,
  bbox_zmin: D.setup.domain_bounding_box[4] as number,
  bbox_zmax: D.setup.domain_bounding_box[5] as number,
  // Box refinement dynamic list — sourced from D.setup.meshing.box_refinement
  box_refinements: Object.entries(D.setup.meshing.box_refinement as unknown as Record<string, { level: number; box: number[] }>).map(
    ([name, v]) => ({
      name,
      level: v.level,
      box_type: "vehicle_bbox_factors" as const,
      box_xmin: v.box[0], box_xmax: v.box[1],
      box_ymin: v.box[2], box_ymax: v.box[3],
      box_zmin: v.box[4], box_zmax: v.box[5],
      parts: "",
      offset_xmin: 0.5, offset_xmax: 0.5,
      offset_ymin: 0.5, offset_ymax: 0.5,
      offset_zmin: 0.5, offset_zmax: 0.5,
    })
  ) as BoxRefinementFormItem[],
  // Offset refinement dynamic list — sourced from D.setup.meshing.offset_refinement
  offset_refinements: Object.entries(D.setup.meshing.offset_refinement as unknown as Record<string, { level: number; normal_distance: number; parts: string[] }>).map(
    ([name, v]) => ({
      name,
      level: v.level,
      normal_distance: v.normal_distance,
      parts: Array.isArray(v.parts) ? v.parts.join(", ") : "",
    })
  ) as OffsetRefinementFormItem[],
  // Custom refinement dynamic list
  custom_refinements: [] as CustomRefinementFormItem[],

  // ── Boundary conditions — ground ──────────────────────────────────────
  ground_height_mode: D.setup_option.boundary_condition.ground.ground_height_mode as "from_geometry" | "absolute",
  ground_height_absolute: D.setup_option.boundary_condition.ground.ground_height_absolute,
  ground_height_offset_from_geom_zMin: D.setup_option.boundary_condition.ground.ground_height_offset_from_geom_zMin,
  ground_patch_active: D.setup_option.boundary_condition.ground.ground_patch_active,
  ground_mode: D.setup_option.boundary_condition.ground.ground_mode as
    | "static" | "rotating_belt_1" | "rotating_belt_5" | "full_moving",
  overset_wheels: D.setup_option.boundary_condition.ground.overset_wheels,
  bl_suction_apply: D.setup_option.boundary_condition.ground.bl_suction.apply,
  bl_suction_no_slip_xmin_pos: D.setup_option.boundary_condition.ground.bl_suction.no_slip_xmin_pos as number | null,
  bl_suction_from_belt_xmin: D.setup_option.boundary_condition.ground.bl_suction.no_slip_xmin_from_belt_xmin,
  bl_suction_xmin_offset: D.setup_option.boundary_condition.ground.bl_suction.bl_xmin_offset,
  belt5_wheel_loc_auto: D.setup_option.boundary_condition.ground.belt5.wheel_belt_location_auto,
  belt5_narrow_fallback: D.setup_option.boundary_condition.ground.belt5.narrow_car_fallback.enabled,
  belt5_narrow_min_gap: D.setup_option.boundary_condition.ground.belt5.narrow_car_fallback.min_belt_gap,
  belt5_center_pos: D.setup_option.boundary_condition.ground.belt5.center_belt_position as "at_wheelbase_center" | "user_specified",
  belt5_center_x: D.setup_option.boundary_condition.ground.belt5.center_belt_x_pos as number | null,
  belt5_wheel_size_x: D.setup_option.boundary_condition.ground.belt5.belt_size_wheel.x,
  belt5_wheel_size_y: D.setup_option.boundary_condition.ground.belt5.belt_size_wheel.y,
  belt5_center_size_x: D.setup_option.boundary_condition.ground.belt5.belt_size_center.x,
  belt5_center_size_y: D.setup_option.boundary_condition.ground.belt5.belt_size_center.y,
  belt5_include_wheel_forces: D.setup_option.boundary_condition.ground.belt5.include_wheel_belt_forces,
  belt1_size_x: D.setup_option.boundary_condition.ground.belt1.belt_size.x,
  belt1_size_y: D.setup_option.boundary_condition.ground.belt1.belt_size.y,
  apply_static_ground_refinement: D.setup_option.boundary_condition.ground.apply_static_ground_refinement,

  // Porous coefficients at template level
  porous_coefficients: [] as PorousCoeffFormItem[],

  // ── Boundary conditions — turbulence generator ────────────────────────
  tg_enable_ground: D.setup_option.boundary_condition.turbulence_generator.enable_ground_tg,
  tg_enable_body: D.setup_option.boundary_condition.turbulence_generator.enable_body_tg,
  tg_ground_num_eddies: D.setup_option.boundary_condition.turbulence_generator.ground_tg_num_eddies,
  tg_ground_intensity: D.setup_option.boundary_condition.turbulence_generator.ground_tg_intensity,
  tg_body_num_eddies: D.setup_option.boundary_condition.turbulence_generator.body_tg_num_eddies,
  tg_body_intensity: D.setup_option.boundary_condition.turbulence_generator.body_tg_intensity,

  // ── Compute flags ─────────────────────────────────────────────────────
  // NOTE: porous_media / turbulence_generator / rotate_wheels / moving_ground
  //   are all auto-derived in compute_engine — no explicit toggle needed.
  compute_adjust_ride_height: D.setup_option.compute.adjust_ride_height,

  // ── Output — full data ────────────────────────────────────────────────
  fd_output_start_time: D.output.full_data.output_start_time as number,
  fd_output_interval: D.output.full_data.output_interval as number,
  fd_file_format: D.output.full_data.file_format as string,
  fd_coarsening_active: D.output.full_data.output_coarsening_active,
  fd_coarsest_target_rl: D.output.full_data.coarsest_target_refinement_level,
  fd_coarsen_by_num_rl: D.output.full_data.coarsen_by_num_refinement_levels,
  fd_merge_output: D.output.full_data.merge_output,
  fd_delete_unmerged: D.output.full_data.delete_unmerged,
  fd_bbox_mode: D.output.full_data.bbox_mode as "from_meshing_box" | "user_defined",
  fd_bbox_source_box: (D.output.full_data.bbox_source_box_name ?? "") as string,
  // Fallback bbox when full_data.bbox is null — form-specific UI default (not in Pydantic)
  fd_bbox_xmin: -10.0,
  fd_bbox_xmax: 30.0,
  fd_bbox_ymin: -15.0,
  fd_bbox_ymax: 15.0,
  fd_bbox_zmin: 0.0,
  fd_bbox_zmax: 8.0,
  // Output variables — sourced from D.output.full_data.output_variables_*
  output_variables_full: { ...D.output.full_data.output_variables_full } as OutputVarsFull,
  output_variables_surface: { ...D.output.full_data.output_variables_surface } as OutputVarsSurface,

  // ── Output — aero coefficients ────────────────────────────────────────
  ac_ref_area_auto: D.output.aero_coefficients.reference_area_auto,
  ac_ref_area: 2.4,       // form-specific fallback when reference_area_auto=false
  ac_ref_length_auto: D.output.aero_coefficients.reference_length_auto,
  ac_ref_length: 2.7,     // form-specific fallback when reference_length_auto=false
  ac_along_axis_active: D.output.aero_coefficients.coefficients_along_axis_active,
  ac_num_sections_x: D.output.aero_coefficients.num_sections_x,
  ac_num_sections_y: D.output.aero_coefficients.num_sections_y,
  ac_num_sections_z: D.output.aero_coefficients.num_sections_z,
  ac_export_bounds_active: D.output.aero_coefficients.export_bounds_active,
  ac_export_bounds_exclude_domain: D.output.aero_coefficients.export_bounds_exclude_domain_parts,

  // ── Output — dynamic lists ────────────────────────────────────────────
  partial_surfaces: [] as PartialSurfaceFormItem[],
  partial_volumes: [] as PartialVolumeFormItem[],
  section_cuts: [] as SectionCutFormItem[],
  probe_files: [] as ProbeFileFormItem[],

  // ── Target names (comma-separated for list fields) ────────────────────
  tn_wheel: D.target_names.wheel.join(", "),
  tn_rim: D.target_names.rim.join(", "),
  tn_baffle: D.target_names.baffle.join(", "),
  tn_windtunnel: D.target_names.windtunnel.join(", "),
  tn_wt_fr_lh: D.target_names.wheel_tire_fr_lh,
  tn_wt_fr_rh: D.target_names.wheel_tire_fr_rh,
  tn_wt_rr_lh: D.target_names.wheel_tire_rr_lh,
  tn_wt_rr_rh: D.target_names.wheel_tire_rr_rh,
  tn_osm_fr_lh: D.target_names.overset_fr_lh,
  tn_osm_fr_rh: D.target_names.overset_fr_rh,
  tn_osm_rr_lh: D.target_names.overset_rr_lh,
  tn_osm_rr_rh: D.target_names.overset_rr_rh,
  tn_tire_roughness: D.target_names.tire_roughness,
};

export type FormValues = typeof FORM_DEFAULTS;

// ---- form validation ---------------------------------------------------------

/** Shared validate rules for all template settings modals. */
export const FORM_VALIDATE: Partial<Record<keyof FormValues, (value: unknown, values: FormValues) => string | null>> = {
  tn_wt_fr_lh: (v, values) =>
    values.ground_mode === "rotating_belt_5" && !(v as string).trim()
      ? "Required when 5-belt mode is active"
      : null,
  tn_wt_fr_rh: (v, values) =>
    values.ground_mode === "rotating_belt_5" && !(v as string).trim()
      ? "Required when 5-belt mode is active"
      : null,
  tn_wt_rr_lh: (v, values) =>
    values.ground_mode === "rotating_belt_5" && !(v as string).trim()
      ? "Required when 5-belt mode is active"
      : null,
  tn_wt_rr_rh: (v, values) =>
    values.ground_mode === "rotating_belt_5" && !(v as string).trim()
      ? "Required when 5-belt mode is active"
      : null,
};

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
  const bbox = setup?.domain_bounding_box ?? [-5, 10, -12, 12, 0, 20];
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
  const boxRefinements: BoxRefinementFormItem[] = [
    ...Object.entries(
      meshingSetup.box_refinement ?? {}
    ).map(([name, v]: [string, any]) => ({
      name,
      level: v.level ?? 1,
      box_type: (v.mode === "user_defined" ? "user_defined" : "vehicle_bbox_factors") as BoxRefinementFormItem["box_type"],
      box_xmin: v.box?.[0] ?? 0,
      box_xmax: v.box?.[1] ?? 0,
      box_ymin: v.box?.[2] ?? 0,
      box_ymax: v.box?.[3] ?? 0,
      box_zmin: v.box?.[4] ?? 0,
      box_zmax: v.box?.[5] ?? 0,
      parts: "",
      offset_xmin: 0.5, offset_xmax: 0.5,
      offset_ymin: 0.5, offset_ymax: 0.5,
      offset_zmin: 0.5, offset_zmax: 0.5,
    })),
    ...Object.entries(
      meshingSetup.part_based_box_refinement ?? {}
    ).map(([name, v]: [string, any]) => ({
      name,
      level: v.level ?? 1,
      box_type: "around_parts" as const,
      box_xmin: 0, box_xmax: 0, box_ymin: 0, box_ymax: 0, box_zmin: 0, box_zmax: 0,
      parts: joinList(v.parts),
      offset_xmin: v.offset_xmin ?? 0.5,
      offset_xmax: v.offset_xmax ?? 0.5,
      offset_ymin: v.offset_ymin ?? 0.5,
      offset_ymax: v.offset_ymax ?? 0.5,
      offset_zmin: v.offset_zmin ?? 0.5,
      offset_zmax: v.offset_zmax ?? 0.5,
    })),
  ];

  // Partial surfaces, volumes, section cuts
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialSurfaces: PartialSurfaceFormItem[] = (out?.partial_surfaces ?? []).map((ps: any) => ({
    name: ps.name ?? "partial_surface",
    output_start_time: ps.output_start_time ?? 1.5,
    output_interval: ps.output_interval ?? 0.3,
    file_format: ps.file_format ?? "h3d",
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
    output_start_time: pv.output_start_time ?? 1.5,
    output_interval: pv.output_interval ?? 0.3,
    file_format: pv.file_format ?? "h3d",
    output_coarsening_active: pv.output_coarsening_active ?? false,
    coarsest_target_refinement_level: pv.coarsest_target_refinement_level ?? 3,
    coarsen_by_num_refinement_levels: pv.coarsen_by_num_refinement_levels ?? 0,
    merge_output: pv.merge_output ?? true,
    delete_unmerged: pv.delete_unmerged ?? true,
    bbox_mode: pv.bbox_mode ?? "user_defined",
    bbox_source_box_name: pv.bbox_source_box_name ?? "",
    bbox_source_parts: joinList(pv.bbox_source_parts),
    bbox_offset_xmin: pv.bbox_offset_xmin ?? 0.0,
    bbox_offset_xmax: pv.bbox_offset_xmax ?? 0.0,
    bbox_offset_ymin: pv.bbox_offset_ymin ?? 0.0,
    bbox_offset_ymax: pv.bbox_offset_ymax ?? 0.0,
    bbox_offset_zmin: pv.bbox_offset_zmin ?? 0.0,
    bbox_offset_zmax: pv.bbox_offset_zmax ?? 0.0,
    bbox: bboxToStr(pv.bbox),
    output_variables: ovPV(pv.output_variables),
  }));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sectionCuts: SectionCutFormItem[] = (out?.section_cuts ?? []).map((sc: any) => ({
    name: sc.name ?? "section_cut",
    output_start_time: sc.output_start_time ?? 1.5,
    output_interval: sc.output_interval ?? 0.3,
    file_format: sc.file_format ?? "h3d",
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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const probeFiles: ProbeFileFormItem[] = (out?.probe_files ?? []).map((pf: any) => ({
    name: pf.name ?? "probe",
    probe_type: pf.probe_type ?? "volume",
    radius: pf.radius ?? 0.0,
    output_frequency: pf.output_frequency ?? 1.0,
    output_start_iteration: pf.output_start_iteration ?? 0,
    scientific_notation: pf.scientific_notation ?? true,
    output_precision: pf.output_precision ?? 7,
    output_variables: {
      pressure: pf.output_variables?.pressure ?? null,
      time_avg_pressure: pf.output_variables?.time_avg_pressure ?? null,
      window_avg_pressure: pf.output_variables?.window_avg_pressure ?? null,
      cp: pf.output_variables?.cp ?? null,
      velocity: pf.output_variables?.velocity ?? null,
      time_avg_velocity: pf.output_variables?.time_avg_velocity ?? null,
      window_avg_velocity: pf.output_variables?.window_avg_velocity ?? null,
      velocity_magnitude: pf.output_variables?.velocity_magnitude ?? null,
      time_avg_velocity_magnitude: pf.output_variables?.time_avg_velocity_magnitude ?? null,
      window_avg_velocity_magnitude: pf.output_variables?.window_avg_velocity_magnitude ?? null,
      wall_shear_stress: pf.output_variables?.wall_shear_stress ?? null,
      time_avg_wall_shear_stress: pf.output_variables?.time_avg_wall_shear_stress ?? null,
      window_avg_wall_shear_stress: pf.output_variables?.window_avg_wall_shear_stress ?? null,
      density: pf.output_variables?.density ?? null,
      time_avg_density: pf.output_variables?.time_avg_density ?? null,
      window_avg_density: pf.output_variables?.window_avg_density ?? null,
      pressure_std: pf.output_variables?.pressure_std ?? null,
      pressure_var: pf.output_variables?.pressure_var ?? null,
    } as ProbeFileOutputVars,
    points: (pf.points ?? []).map((pt: any) => ({
      x_pos: pt.x_pos ?? 0.0,
      y_pos: pt.y_pos ?? 0.0,
      z_pos: pt.z_pos ?? 0.0,
      description: pt.description ?? "",
    })),
  }));

  // Porous coefficients
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const porousCoeffs: PorousCoeffFormItem[] = (settings?.porous_coefficients ?? []).map((p: any) => ({
    part_name: p.part_name ?? "",
    inertial_resistance: p.inertial_resistance ?? 0.0,
    viscous_resistance: p.viscous_resistance ?? 0.0,
  }));

  return {
    inflow_velocity: sp.inflow_velocity ?? FORM_DEFAULTS.inflow_velocity,
    density: sp.density ?? FORM_DEFAULTS.density,
    dynamic_viscosity: sp.dynamic_viscosity ?? FORM_DEFAULTS.dynamic_viscosity,
    temperature: sp.temperature ?? FORM_DEFAULTS.temperature,
    specific_gas_constant: sp.specific_gas_constant ?? FORM_DEFAULTS.specific_gas_constant,
    mach_factor: sp.mach_factor ?? FORM_DEFAULTS.mach_factor,
    num_ramp_up_iter: sp.num_ramp_up_iter ?? FORM_DEFAULTS.num_ramp_up_iter,
    coarsest_voxel_size: sp.coarsest_voxel_size ?? FORM_DEFAULTS.coarsest_voxel_size,
    number_of_resolution: sp.number_of_resolution ?? FORM_DEFAULTS.number_of_resolution,
    simulation_time: sp.simulation_time ?? FORM_DEFAULTS.simulation_time,
    simulation_time_FP: sp.simulation_time_FP ?? FORM_DEFAULTS.simulation_time_FP,
    start_averaging_time: sp.start_averaging_time ?? FORM_DEFAULTS.start_averaging_time,
    avg_window_size: sp.avg_window_size ?? FORM_DEFAULTS.avg_window_size,
    yaw_angle: sp.yaw_angle ?? FORM_DEFAULTS.yaw_angle,
    temperature_degree: so?.simulation?.temperature_degree ?? FORM_DEFAULTS.temperature_degree,
    simulation_time_with_FP: so?.simulation?.simulation_time_with_FP ?? FORM_DEFAULTS.simulation_time_with_FP,

    triangle_splitting: m.triangle_splitting ?? FORM_DEFAULTS.triangle_splitting,
    ts_max_absolute_edge_length: (m.max_absolute_edge_length as number | undefined) ?? FORM_DEFAULTS.ts_max_absolute_edge_length,
    max_relative_edge_length: m.max_relative_edge_length ?? FORM_DEFAULTS.max_relative_edge_length,
    triangle_splitting_instances: ((m.triangle_splitting_instances ?? []) as any[]).map((inst) => ({
      name: inst.name,
      active: inst.active ?? true,
      max_absolute_edge_length: inst.max_absolute_edge_length ?? 0.0,
      max_relative_edge_length: inst.max_relative_edge_length ?? 9.0,
      parts: joinList(inst.parts),
    })) as TriangleSplittingInstanceFormItem[],
    refinement_level_transition_layers: m.refinement_level_transition_layers ?? FORM_DEFAULTS.refinement_level_transition_layers,
    box_refinement_porous: m.box_refinement_porous ?? FORM_DEFAULTS.box_refinement_porous,
    bbox_xmin: bbox[0] ?? FORM_DEFAULTS.bbox_xmin,
    bbox_xmax: bbox[1] ?? FORM_DEFAULTS.bbox_xmax,
    bbox_ymin: bbox[2] ?? FORM_DEFAULTS.bbox_ymin,
    bbox_ymax: bbox[3] ?? FORM_DEFAULTS.bbox_ymax,
    bbox_zmin: bbox[4] ?? FORM_DEFAULTS.bbox_zmin,
    bbox_zmax: bbox[5] ?? FORM_DEFAULTS.bbox_zmax,
    box_refinements: boxRefinements,
    offset_refinements: offsetRefinements,
    custom_refinements: customRefinements,

    ground_height_mode: gc.ground_height_mode ?? FORM_DEFAULTS.ground_height_mode,
    ground_height_absolute: gc.ground_height_absolute ?? FORM_DEFAULTS.ground_height_absolute,
    ground_height_offset_from_geom_zMin: gc.ground_height_offset_from_geom_zMin ?? FORM_DEFAULTS.ground_height_offset_from_geom_zMin,
    ground_patch_active: gc.ground_patch_active ?? FORM_DEFAULTS.ground_patch_active,
    ground_mode: gc.ground_mode ?? FORM_DEFAULTS.ground_mode,
    overset_wheels: gc.overset_wheels ?? FORM_DEFAULTS.overset_wheels,
    bl_suction_apply: bl.apply ?? FORM_DEFAULTS.bl_suction_apply,
    bl_suction_no_slip_xmin_pos: bl.no_slip_xmin_pos ?? FORM_DEFAULTS.bl_suction_no_slip_xmin_pos,
    bl_suction_from_belt_xmin: bl.no_slip_xmin_from_belt_xmin ?? FORM_DEFAULTS.bl_suction_from_belt_xmin,
    bl_suction_xmin_offset: bl.bl_xmin_offset ?? FORM_DEFAULTS.bl_suction_xmin_offset,
    belt5_wheel_loc_auto: b5.wheel_belt_location_auto ?? FORM_DEFAULTS.belt5_wheel_loc_auto,
    belt5_narrow_fallback: b5.narrow_car_fallback?.enabled ?? FORM_DEFAULTS.belt5_narrow_fallback,
    belt5_narrow_min_gap: b5.narrow_car_fallback?.min_belt_gap ?? FORM_DEFAULTS.belt5_narrow_min_gap,
    belt5_center_pos: b5.center_belt_position ?? FORM_DEFAULTS.belt5_center_pos,
    belt5_center_x: b5.center_belt_x_pos ?? FORM_DEFAULTS.belt5_center_x,
    belt5_wheel_size_x: b5.belt_size_wheel?.x ?? FORM_DEFAULTS.belt5_wheel_size_x,
    belt5_wheel_size_y: b5.belt_size_wheel?.y ?? FORM_DEFAULTS.belt5_wheel_size_y,
    belt5_center_size_x: b5.belt_size_center?.x ?? FORM_DEFAULTS.belt5_center_size_x,
    belt5_center_size_y: b5.belt_size_center?.y ?? FORM_DEFAULTS.belt5_center_size_y,
    belt5_include_wheel_forces: b5.include_wheel_belt_forces ?? FORM_DEFAULTS.belt5_include_wheel_forces,
    belt1_size_x: b1.belt_size?.x ?? FORM_DEFAULTS.belt1_size_x,
    belt1_size_y: b1.belt_size?.y ?? FORM_DEFAULTS.belt1_size_y,
    apply_static_ground_refinement: gc.apply_static_ground_refinement ?? FORM_DEFAULTS.apply_static_ground_refinement,
    porous_coefficients: porousCoeffs,

    tg_enable_ground: tg.enable_ground_tg ?? FORM_DEFAULTS.tg_enable_ground,
    tg_enable_body: tg.enable_body_tg ?? FORM_DEFAULTS.tg_enable_body,
    tg_ground_num_eddies: tg.ground_tg_num_eddies ?? FORM_DEFAULTS.tg_ground_num_eddies,
    tg_ground_intensity: tg.ground_tg_intensity ?? FORM_DEFAULTS.tg_ground_intensity,
    tg_body_num_eddies: tg.body_tg_num_eddies ?? FORM_DEFAULTS.tg_body_num_eddies,
    tg_body_intensity: tg.body_tg_intensity ?? FORM_DEFAULTS.tg_body_intensity,

    compute_adjust_ride_height: cp.adjust_ride_height ?? FORM_DEFAULTS.compute_adjust_ride_height,

    fd_output_start_time: fd.output_start_time ?? FORM_DEFAULTS.fd_output_start_time,
    fd_output_interval: fd.output_interval ?? FORM_DEFAULTS.fd_output_interval,
    fd_file_format: (fd.file_format ?? "h3d") as string,
    fd_coarsening_active: fd.output_coarsening_active ?? FORM_DEFAULTS.fd_coarsening_active,
    fd_coarsest_target_rl: fd.coarsest_target_refinement_level ?? FORM_DEFAULTS.fd_coarsest_target_rl,
    fd_coarsen_by_num_rl: fd.coarsen_by_num_refinement_levels ?? FORM_DEFAULTS.fd_coarsen_by_num_rl,
    fd_merge_output: fd.merge_output ?? FORM_DEFAULTS.fd_merge_output,
    fd_delete_unmerged: fd.delete_unmerged ?? FORM_DEFAULTS.fd_delete_unmerged,
    fd_bbox_mode: fd.bbox_mode ?? FORM_DEFAULTS.fd_bbox_mode,
    fd_bbox_source_box: fd.bbox_source_box_name ?? FORM_DEFAULTS.fd_bbox_source_box,
    fd_bbox_xmin: fdBbox[0],
    fd_bbox_xmax: fdBbox[1],
    fd_bbox_ymin: fdBbox[2],
    fd_bbox_ymax: fdBbox[3],
    fd_bbox_zmin: fdBbox[4],
    fd_bbox_zmax: fdBbox[5],
    output_variables_full: ovFull(fd.output_variables_full),
    output_variables_surface: ovSurface(fd.output_variables_surface),

    ac_ref_area_auto: ac.reference_area_auto ?? FORM_DEFAULTS.ac_ref_area_auto,
    ac_ref_area: ac.reference_area ?? FORM_DEFAULTS.ac_ref_area,
    ac_ref_length_auto: ac.reference_length_auto ?? FORM_DEFAULTS.ac_ref_length_auto,
    ac_ref_length: ac.reference_length ?? FORM_DEFAULTS.ac_ref_length,
    ac_along_axis_active: ac.coefficients_along_axis_active ?? FORM_DEFAULTS.ac_along_axis_active,
    ac_num_sections_x: ac.num_sections_x ?? FORM_DEFAULTS.ac_num_sections_x,
    ac_num_sections_y: ac.num_sections_y ?? FORM_DEFAULTS.ac_num_sections_y,
    ac_num_sections_z: ac.num_sections_z ?? FORM_DEFAULTS.ac_num_sections_z,
    ac_export_bounds_active: ac.export_bounds_active ?? FORM_DEFAULTS.ac_export_bounds_active,
    ac_export_bounds_exclude_domain: ac.export_bounds_exclude_domain_parts ?? FORM_DEFAULTS.ac_export_bounds_exclude_domain,

    partial_surfaces: partialSurfaces,
    partial_volumes: partialVolumes,
    section_cuts: sectionCuts,
    probe_files: probeFiles,

    tn_wheel: joinList(tn.wheel),
    tn_rim: joinList(tn.rim),
    tn_baffle: joinList(tn.baffle),
    tn_windtunnel: joinList(tn.windtunnel),
    tn_wt_fr_lh: tn.wheel_tire_fr_lh ?? FORM_DEFAULTS.tn_wt_fr_lh,
    tn_wt_fr_rh: tn.wheel_tire_fr_rh ?? FORM_DEFAULTS.tn_wt_fr_rh,
    tn_wt_rr_lh: tn.wheel_tire_rr_lh ?? FORM_DEFAULTS.tn_wt_rr_lh,
    tn_wt_rr_rh: tn.wheel_tire_rr_rh ?? FORM_DEFAULTS.tn_wt_rr_rh,
    tn_osm_fr_lh: tn.overset_fr_lh ?? FORM_DEFAULTS.tn_osm_fr_lh,
    tn_osm_fr_rh: tn.overset_fr_rh ?? FORM_DEFAULTS.tn_osm_fr_rh,
    tn_osm_rr_lh: tn.overset_rr_lh ?? FORM_DEFAULTS.tn_osm_rr_lh,
    tn_osm_rr_rh: tn.overset_rr_rh ?? FORM_DEFAULTS.tn_osm_rr_rh,
    tn_tire_roughness: tn.tire_roughness ?? FORM_DEFAULTS.tn_tire_roughness,
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

  // Build box refinement dicts from form list (split by box_type)
  const boxRefinementDict: Record<string, object> = {};
  const partBasedBoxRefinementDict: Record<string, object> = {};
  for (const item of values.box_refinements) {
    if (!item.name) continue;
    if (item.box_type === "around_parts") {
      partBasedBoxRefinementDict[item.name] = {
        level: item.level,
        parts: splitList(item.parts),
        offset_xmin: item.offset_xmin,
        offset_xmax: item.offset_xmax,
        offset_ymin: item.offset_ymin,
        offset_ymax: item.offset_ymax,
        offset_zmin: item.offset_zmin,
        offset_zmax: item.offset_zmax,
      };
    } else {
      boxRefinementDict[item.name] = {
        level: item.level,
        mode: item.box_type,
        box: [item.box_xmin, item.box_xmax, item.box_ymin, item.box_ymax, item.box_zmin, item.box_zmax],
      };
    }
  }

  // Preserve box_refinement from existing (not editable in form yet)
  const existingMeshing = existingSettings?.setup?.meshing ?? {};

  // Build partial surfaces
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const partialSurfaces = values.partial_surfaces.map((ps: any) => ({
    name: ps.name,
    output_start_time: ps.output_start_time,
    output_interval: ps.output_interval,
    file_format: ps.file_format,
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
    file_format: pv.file_format,
    output_coarsening_active: pv.output_coarsening_active,
    coarsest_target_refinement_level: pv.coarsest_target_refinement_level,
    coarsen_by_num_refinement_levels: pv.coarsen_by_num_refinement_levels,
    merge_output: pv.merge_output,
    delete_unmerged: pv.delete_unmerged,
    bbox_mode: pv.bbox_mode,
    bbox_source_box_name: pv.bbox_mode === "from_meshing_box" ? pv.bbox_source_box_name || null : null,
    bbox_source_parts: pv.bbox_mode === "around_parts" ? splitList(pv.bbox_source_parts) : [],
    bbox_offset_xmin: pv.bbox_mode === "around_parts" ? pv.bbox_offset_xmin : 0.0,
    bbox_offset_xmax: pv.bbox_mode === "around_parts" ? pv.bbox_offset_xmax : 0.0,
    bbox_offset_ymin: pv.bbox_mode === "around_parts" ? pv.bbox_offset_ymin : 0.0,
    bbox_offset_ymax: pv.bbox_mode === "around_parts" ? pv.bbox_offset_ymax : 0.0,
    bbox_offset_zmin: pv.bbox_mode === "around_parts" ? pv.bbox_offset_zmin : 0.0,
    bbox_offset_zmax: pv.bbox_mode === "around_parts" ? pv.bbox_offset_zmax : 0.0,
    bbox: pv.bbox_mode === "user_defined" ? strToBbox(pv.bbox) : null,
    output_variables: pv.output_variables,
  }));

  // Build section cuts
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sectionCuts = values.section_cuts.map((sc: any) => ({
    name: sc.name,
    output_start_time: sc.output_start_time,
    output_interval: sc.output_interval,
    file_format: sc.file_format,
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

  // Build probe files
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const probeFiles = values.probe_files.map((pf: any) => ({
    name: pf.name,
    probe_type: pf.probe_type,
    radius: pf.radius,
    output_frequency: pf.output_frequency,
    output_start_iteration: pf.output_start_iteration,
    scientific_notation: pf.scientific_notation,
    output_precision: pf.output_precision,
    output_variables: pf.output_variables,
    points: pf.points,
  }));

  return {
    setup_option: {
      simulation: {
        temperature_degree: values.temperature_degree,
        simulation_time_with_FP: values.simulation_time_with_FP,
      },
      meshing: {
        triangle_splitting: values.triangle_splitting,
        max_absolute_edge_length: values.ts_max_absolute_edge_length,
        max_relative_edge_length: values.max_relative_edge_length,
        triangle_splitting_instances: values.triangle_splitting_instances.map((inst) => ({
          name: inst.name,
          active: inst.active,
          max_absolute_edge_length: inst.max_absolute_edge_length,
          max_relative_edge_length: inst.max_relative_edge_length,
          parts: splitList(inst.parts),
        })),
        refinement_level_transition_layers: values.refinement_level_transition_layers,
        domain_bounding_box_relative: true,
        box_offset_relative: true,
        box_refinement_porous: values.box_refinement_porous,
      },
      boundary_condition: {
        ground: {
          ground_height_mode: values.ground_height_mode,
          ground_height_absolute: values.ground_height_absolute,
          ground_height_offset_from_geom_zMin: values.ground_height_offset_from_geom_zMin,
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
        box_refinement: boxRefinementDict,
        part_box_refinement: existingMeshing.part_box_refinement ?? {},
        part_based_box_refinement: partBasedBoxRefinementDict,
        offset_refinement: offsetRefinementDict,
        custom_refinement: customRefinementDict,
      },
    },
    output: {
      full_data: {
        output_start_time: values.fd_output_start_time,
        output_interval: values.fd_output_interval,
        file_format: values.fd_file_format,
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
      probe_files: probeFiles,
    },
    target_names: {
      wheel: splitList(values.tn_wheel),
      rim: splitList(values.tn_rim),
      baffle: splitList(values.tn_baffle),
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
