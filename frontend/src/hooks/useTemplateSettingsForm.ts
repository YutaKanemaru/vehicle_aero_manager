/**
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
  section_cuts: [] as SectionCutFormItem[],  probe_files: [] as ProbeFileFormItem[],
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
    probe_files: probeFiles,

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
      probe_files: probeFiles,
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
