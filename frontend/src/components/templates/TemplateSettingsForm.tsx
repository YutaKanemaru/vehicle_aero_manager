/**
 * Shared template settings form fields.
 * Used by both TemplateCreateModal and TemplateVersionCreateModal.
 */
import {
  Tabs,
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
import type { ReactNode } from "react";
import type { UseFormReturnType } from "@mantine/form";
import type {
  FormValues,
  OffsetRefinementFormItem,
  CustomRefinementFormItem,
  BoxRefinementFormItem,
  PartialSurfaceFormItem,
  PartialVolumeFormItem,
  SectionCutFormItem,
  ProbeFileFormItem,
  ProbeFileOutputVars,
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
  generalContent?: ReactNode;
  readOnly?: boolean;
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

// ---- Box refinement defaults (shared between aero & GHN) -------------------

function getBoxRefinementDefaults(): BoxRefinementFormItem[] {
  return [
    { name: "Box_RL1", level: 1, box_xmin: -1, box_xmax: 3, box_ymin: -1, box_ymax: 1, box_zmin: -0.2, box_zmax: 1.5 },
    { name: "Box_RL2", level: 2, box_xmin: -0.5, box_xmax: 1.5, box_ymin: -0.75, box_ymax: 0.75, box_zmin: -0.2, box_zmax: 1 },
    { name: "Box_RL3", level: 3, box_xmin: -0.3, box_xmax: 1, box_ymin: -0.5, box_ymax: 0.5, box_zmin: -0.2, box_zmax: 0.75 },
    { name: "Box_RL4", level: 4, box_xmin: -0.2, box_xmax: 0.6, box_ymin: -0.3, box_ymax: 0.3, box_zmin: -0.2, box_zmax: 0.5 },
    { name: "Box_RL5", level: 5, box_xmin: -0.1, box_xmax: 0.3, box_ymin: -0.15, box_ymax: 0.15, box_zmin: -0.2, box_zmax: 0.25 },
  ];
}

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

export function TemplateSettingsForm({ form, simType, generalContent, readOnly }: Props) {
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

  // ── Probe file helpers ────────────────────────────────────────────────────
  const DEFAULT_PROBE_VARS: ProbeFileOutputVars = {
    pressure: null, time_avg_pressure: null, window_avg_pressure: null,
    cp: null, velocity: null, time_avg_velocity: null, window_avg_velocity: null,
    velocity_magnitude: null, time_avg_velocity_magnitude: null,
    window_avg_velocity_magnitude: null,
    wall_shear_stress: null, time_avg_wall_shear_stress: null,
    window_avg_wall_shear_stress: null,
    density: null, time_avg_density: null, window_avg_density: null,
    pressure_std: null, pressure_var: null,
  };

  const addProbeFile = () =>
    form.insertListItem("probe_files", {
      name: `probe_${form.values.probe_files.length + 1}`,
      probe_type: "volume",
      radius: 0.0,
      output_frequency: 1.0,
      output_start_iteration: 0,
      scientific_notation: true,
      output_precision: 7,
      output_variables: { ...DEFAULT_PROBE_VARS },
      points: [],
    } as ProbeFileFormItem);

  const importProbeCSV = (idx: number, csvText: string) => {
    const lines = csvText.split(/\r?\n/).filter((l) => l.trim() !== "");
    const points = lines.map((line) => {
      const parts = line.split(";");
      return {
        x_pos: parseFloat(parts[0] ?? "0") || 0,
        y_pos: parseFloat(parts[1] ?? "0") || 0,
        z_pos: parseFloat(parts[2] ?? "0") || 0,
        description: parts[3]?.trim() ?? "",
      };
    });
    form.setFieldValue(`probe_files.${idx}.points`, points);
  };

  const exportProbeCSV = (pf: ProbeFileFormItem) => {
    const csvLines = pf.points.map(
      (pt) => `${pt.x_pos};${pt.y_pos};${pt.z_pos};${pt.description}`
    );
    const blob = new Blob([csvLines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${pf.name}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const setProbeVar = (
    idx: number,
    varName: keyof ProbeFileOutputVars,
    val: boolean | null
  ) => {
    form.setFieldValue(`probe_files.${idx}.output_variables.${varName}`, val);
  };

  const PW = readOnly
    ? ({ children }: { children: ReactNode }) => (
        <fieldset disabled style={{ border: "none", padding: 0, margin: 0 }}>
          {children}
        </fieldset>
      )
    : ({ children }: { children: ReactNode }) => <>{children}</>;

  return (
    <Tabs defaultValue={generalContent ? "general" : "sim"}>
      <Tabs.List>
        {generalContent && <Tabs.Tab value="general">General</Tabs.Tab>}
        <Tabs.Tab value="sim">Simulation Run Parameters</Tabs.Tab>
        <Tabs.Tab value="meshing">Meshing</Tabs.Tab>
        <Tabs.Tab value="bc">Boundary Conditions</Tabs.Tab>
        <Tabs.Tab value="output">Output</Tabs.Tab>
        <Tabs.Tab value="targets">Target Part Names</Tabs.Tab>
      </Tabs.List>
      {generalContent && (
        <Tabs.Panel value="general" pt="md">
          <PW>{generalContent}</PW>
        </Tabs.Panel>
      )}
      {/* ── Simulation Run Parameters ──────────────────────────────── */}
      <Tabs.Panel value="sim" pt="md">
        <PW><Stack gap="xs">
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
          </Stack></PW>
      </Tabs.Panel>

      {/* ── Meshing ──────────────────────────────────────────────────── */}
      <Tabs.Panel value="meshing" pt="md">
        <PW><Stack gap="xs">
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

            <Divider label="Domain bounding box factors" labelPosition="center" />
            <Group justify="flex-end">
              <Button size="xs" variant="light" onClick={() => {
                form.setFieldValue("bbox_xmin", -5);
                form.setFieldValue("bbox_xmax", 10);
                form.setFieldValue("bbox_ymin", -12);
                form.setFieldValue("bbox_ymax", 12);
                form.setFieldValue("bbox_zmin", 0);
                form.setFieldValue("bbox_zmax", 20);
              }}>
                Restore defaults
              </Button>
            </Group>
            <SimpleGrid cols={3}>
              <NumberInput label="X min factor" step={0.5} {...form.getInputProps("bbox_xmin")} />
              <NumberInput label="X max factor" step={0.5} {...form.getInputProps("bbox_xmax")} />
              <NumberInput label="Y min factor" step={0.5} {...form.getInputProps("bbox_ymin")} />
            </SimpleGrid>
            <SimpleGrid cols={3}>
              <NumberInput label="Y max factor" step={0.5} {...form.getInputProps("bbox_ymax")} />
              <NumberInput label="Z min factor" step={0.5} {...form.getInputProps("bbox_zmin")} />
              <NumberInput label="Z max factor" step={0.5} {...form.getInputProps("bbox_zmax")} />
            </SimpleGrid>

            {/* Box refinement dynamic list */}
            <Divider label="Box Refinement (relative to vehicle size)" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Box refinement zones ({form.values.box_refinements.length})</Text>
              <Group gap="xs">
                <Button size="xs" variant="light" onClick={() => {
                  const defaults = getBoxRefinementDefaults();
                  const existing = form.values.box_refinements.filter(
                    (b) => !defaults.some((d) => d.name === b.name)
                  );
                  form.setFieldValue("box_refinements", [...defaults, ...existing]);
                }}>
                  Restore defaults
                </Button>
                <Button size="xs" leftSection={<IconPlus size={12} />} onClick={() =>
                  form.insertListItem("box_refinements", {
                    name: `Box_RL${form.values.box_refinements.length + 1}`,
                    level: form.values.box_refinements.length + 1,
                    box_xmin: 0, box_xmax: 0, box_ymin: 0, box_ymax: 0, box_zmin: 0, box_zmax: 0,
                  } as BoxRefinementFormItem)
                }>
                  Add
                </Button>
              </Group>
            </Group>
            {form.values.box_refinements.map((_, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={4}>
                  <Badge size="sm" variant="outline">Box {idx + 1}</Badge>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("box_refinements", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <SimpleGrid cols={2}>
                  <TextInput label="Name" {...form.getInputProps(`box_refinements.${idx}.name`)} />
                  <NumberInput label="Refinement level" {...form.getInputProps(`box_refinements.${idx}.level`)} />
                </SimpleGrid>
                <SimpleGrid cols={3}>
                  <NumberInput label="X min" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_xmin`)} />
                  <NumberInput label="X max" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_xmax`)} />
                  <NumberInput label="Y min" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_ymin`)} />
                </SimpleGrid>
                <SimpleGrid cols={3}>
                  <NumberInput label="Y max" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_ymax`)} />
                  <NumberInput label="Z min" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_zmin`)} />
                  <NumberInput label="Z max" decimalScale={2} step={0.1} {...form.getInputProps(`box_refinements.${idx}.box_zmax`)} />
                </SimpleGrid>
              </Paper>
            ))}

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
          </Stack></PW>
      </Tabs.Panel>

      {/* ── Boundary Conditions ───────────────────────────────────────── */}
      <Tabs.Panel value="bc" pt="md">
        <PW><Stack gap="sm">
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
            {form.values.ground_height_mode === "from_geometry" && (
              <NumberInput
                label="Ground height offset from geometry z_min (m)"
                description="ground_height = STL z_min + offset  (e.g. 0.01 for 10 mm above z_min)"
                step={0.001}
                decimalScale={4}
                {...form.getInputProps("ground_height_offset_from_geom_zMin")}
              />
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
          </Stack></PW>
      </Tabs.Panel>

      {/* ── Output ───────────────────────────────────────────────────── */}
      <Tabs.Panel value="output" pt="md">
        <PW><Stack gap="sm">
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

            {/* Probe Files */}
            <Divider label="Probe Files" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Probe file instances ({form.values.probe_files.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addProbeFile}>Add</Button>
            </Group>
            <Text size="xs" c="dimmed">
              Each probe file contains multiple probe locations (x;y;z;description CSV format).
              Define probe points here — the CSV is generated automatically alongside output.xml.
            </Text>
            {form.values.probe_files.map((pf, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Group justify="space-between" mb={6}>
                  <Title order={6}>{pf.name || `Probe ${idx + 1}`}</Title>
                  <ActionIcon color="red" size="sm" variant="subtle"
                    onClick={() => form.removeListItem("probe_files", idx)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
                <Stack gap="xs">
                  <SimpleGrid cols={2}>
                    <TextInput label="Name (used as CSV filename)" {...form.getInputProps(`probe_files.${idx}.name`)} />
                    <Select label="Type" data={["volume", "surface"]}
                      {...form.getInputProps(`probe_files.${idx}.probe_type`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={3}>
                    <NumberInput label="Radius (m)" decimalScale={4} step={0.01}
                      {...form.getInputProps(`probe_files.${idx}.radius`)} />
                    <NumberInput label="Output frequency (iterations)" decimalScale={2} step={1}
                      {...form.getInputProps(`probe_files.${idx}.output_frequency`)} />
                    <NumberInput label="Output start iteration" step={1}
                      {...form.getInputProps(`probe_files.${idx}.output_start_iteration`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Scientific notation" size="sm"
                      {...form.getInputProps(`probe_files.${idx}.scientific_notation`, { type: "checkbox" })} />
                    <NumberInput label="Output precision (significant digits)" step={1} min={1} max={15}
                      {...form.getInputProps(`probe_files.${idx}.output_precision`)} />
                  </SimpleGrid>

                  {/* Output variables */}
                  <Divider label="Optional output variables (checked = explicitly request)" labelPosition="center" />
                  <Text size="xs" c="dimmed">
                    Volume defaults: pressure, velocity (x/y/z), velocity_magnitude. Surface default: cp.
                    Check optional variables to add them; unchecked means use solver default.
                  </Text>
                  {(() => {
                    const isVolume = pf.probe_type === "volume";
                    type VarRow = { key: keyof ProbeFileOutputVars; label: string; surfaceOnly?: boolean };
                    const varRows: VarRow[] = [
                      { key: "pressure", label: "pressure" },
                      { key: "time_avg_pressure", label: "time_avg_pressure" },
                      { key: "window_avg_pressure", label: "window_avg_pressure" },
                      { key: "cp", label: "cp" },
                      { key: "velocity", label: "velocity (x,y,z)" },
                      { key: "time_avg_velocity", label: "time_avg_velocity" },
                      { key: "window_avg_velocity", label: "window_avg_velocity" },
                      { key: "velocity_magnitude", label: "velocity_magnitude" },
                      { key: "time_avg_velocity_magnitude", label: "time_avg_velocity_magnitude" },
                      { key: "window_avg_velocity_magnitude", label: "window_avg_velocity_magnitude" },
                      { key: "wall_shear_stress", label: "wall_shear_stress", surfaceOnly: true },
                      { key: "time_avg_wall_shear_stress", label: "time_avg_wall_shear_stress", surfaceOnly: true },
                      { key: "window_avg_wall_shear_stress", label: "window_avg_wall_shear_stress", surfaceOnly: true },
                      { key: "density", label: "density" },
                      { key: "time_avg_density", label: "time_avg_density" },
                      { key: "window_avg_density", label: "window_avg_density" },
                      { key: "pressure_std", label: "pressure_std" },
                      { key: "pressure_var", label: "pressure_var" },
                    ];
                    const visible = varRows.filter((r) => !r.surfaceOnly || !isVolume);
                    return (
                      <SimpleGrid cols={3}>
                        {visible.map((r) => (
                          <Checkbox
                            key={r.key}
                            label={r.label}
                            size="xs"
                            checked={pf.output_variables[r.key] === true}
                            onChange={(e) =>
                              setProbeVar(idx, r.key, e.currentTarget.checked ? true : null)
                            }
                          />
                        ))}
                      </SimpleGrid>
                    );
                  })()}

                  {/* Probe Points */}
                  <Divider label={`Probe points (${pf.points.length})`} labelPosition="center" />
                  <Group gap="xs">
                    <Button size="xs" leftSection={<IconPlus size={12} />}
                      onClick={() => form.insertListItem(`probe_files.${idx}.points`, {
                        x_pos: 0.0, y_pos: 0.0, z_pos: 0.0, description: "",
                      })}>
                      Add point
                    </Button>
                    <Button size="xs" variant="light" component="label">
                      Import CSV
                      <input
                        type="file"
                        accept=".csv,.txt"
                        style={{ display: "none" }}
                        onChange={(e) => {
                          const file = e.currentTarget.files?.[0];
                          if (!file) return;
                          const reader = new FileReader();
                          reader.onload = (ev) =>
                            importProbeCSV(idx, (ev.target?.result as string) ?? "");
                          reader.readAsText(file);
                          e.currentTarget.value = "";
                        }}
                      />
                    </Button>
                    {pf.points.length > 0 && (
                      <Button size="xs" variant="light" onClick={() => exportProbeCSV(pf)}>
                        Export CSV
                      </Button>
                    )}
                  </Group>
                  <Text size="xs" c="dimmed">CSV format per line: x_pos;y_pos;z_pos;description (no header)</Text>
                  {pf.points.map((_pt, pidx) => (
                    <Paper key={pidx} withBorder p="xs" bg="gray.0">
                      <Group justify="space-between" mb={4}>
                        <Text size="xs" fw={500}>Point #{pidx + 1}</Text>
                        <ActionIcon color="red" size="xs" variant="subtle"
                          onClick={() => form.removeListItem(`probe_files.${idx}.points`, pidx)}>
                          <IconTrash size={12} />
                        </ActionIcon>
                      </Group>
                      <SimpleGrid cols={4}>
                        <NumberInput label="X (m)" decimalScale={4} step={0.01}
                          {...form.getInputProps(`probe_files.${idx}.points.${pidx}.x_pos`)} />
                        <NumberInput label="Y (m)" decimalScale={4} step={0.01}
                          {...form.getInputProps(`probe_files.${idx}.points.${pidx}.y_pos`)} />
                        <NumberInput label="Z (m)" decimalScale={4} step={0.01}
                          {...form.getInputProps(`probe_files.${idx}.points.${pidx}.z_pos`)} />
                        <TextInput label="Description"
                          {...form.getInputProps(`probe_files.${idx}.points.${pidx}.description`)} />
                      </SimpleGrid>
                    </Paper>
                  ))}
                </Stack>
              </Paper>
            ))}
          </Stack></PW>
      </Tabs.Panel>

      {/* ── Target Part Names ─────────────────────────────────────────── */}
      <Tabs.Panel value="targets" pt="md">
        <PW><Stack gap="xs">
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
          </Stack></PW>
      </Tabs.Panel>
    </Tabs>
  );
}
