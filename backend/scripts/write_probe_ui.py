#!/usr/bin/env python3
"""
Patch TemplateSettingsForm.tsx to add:
1. ProbeFileFormItem / ProbeFileOutputVars imports
2. addProbeFile helper (after addSectionCut)
3. Probe Files accordion section (after Section Cuts)
"""
import re
from pathlib import Path

FORM_FILE = Path(__file__).parents[2] / "frontend/src/components/templates/TemplateSettingsForm.tsx"

src = FORM_FILE.read_text(encoding="utf-8")

# ── 1. Add imports ───────────────────────────────────────────────────────────
OLD_IMPORT = '  SectionCutFormItem,\n  PorousCoeffFormItem,\n  OutputVarsFull,\n  OutputVarsSurface,\n  OutputVarsPartialSurface,\n  OutputVarsPartialVolume,\n  OutputVarsSectionCut,'
NEW_IMPORT = '''  SectionCutFormItem,
  ProbeFileFormItem,
  ProbeFileOutputVars,
  PorousCoeffFormItem,
  OutputVarsFull,
  OutputVarsSurface,
  OutputVarsPartialSurface,
  OutputVarsPartialVolume,
  OutputVarsSectionCut,'''
assert OLD_IMPORT in src, "Import block not found"
src = src.replace(OLD_IMPORT, NEW_IMPORT, 1)

# ── 2. Add addProbeFile helper ──────────────────────────────────────────────
OLD_SECTION_CUT_HELPER_END = '''    } as SectionCutFormItem);

  return ('''
NEW_SECTION_CUT_HELPER_END = '''    } as SectionCutFormItem);

  // ── Probe file helpers ──────────────────────────────────────────────────
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
    const lines = csvText.split(/\\r?\\n/).filter((l) => l.trim() !== "");
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
    const blob = new Blob([csvLines.join("\\n")], { type: "text/csv" });
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

  return ('''

assert OLD_SECTION_CUT_HELPER_END in src, "addSectionCut end not found"
src = src.replace(OLD_SECTION_CUT_HELPER_END, NEW_SECTION_CUT_HELPER_END, 1)

# ── 3. Add Probe Files UI section before Target Part Names accordion ─────────
PROBE_UI = '''
            {/* Probe Files */}
            <Divider label="Probe Files" labelPosition="center" />
            <Group justify="space-between">
              <Text size="sm" fw={500}>Probe file instances ({form.values.probe_files.length})</Text>
              <Button size="xs" leftSection={<IconPlus size={12} />} onClick={addProbeFile}>Add</Button>
            </Group>
            <Text size="xs" c="dimmed">
              Each probe file contains multiple probe locations loaded from a CSV (x;y;z;description).
              Define probe points here — the CSV is generated automatically alongside the XML.
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
                    <TextInput label="Name (used as filename)" {...form.getInputProps(`probe_files.${idx}.name`)} />
                    <Select label="Type" data={["volume", "surface"]}
                      {...form.getInputProps(`probe_files.${idx}.probe_type`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={3}>
                    <NumberInput label="Radius (m)" decimalScale={4} step={0.01}
                      {...form.getInputProps(`probe_files.${idx}.radius`)} />
                    <NumberInput label="Output frequency (iter)" decimalScale={2} step={1}
                      {...form.getInputProps(`probe_files.${idx}.output_frequency`)} />
                    <NumberInput label="Output start iteration" step={1}
                      {...form.getInputProps(`probe_files.${idx}.output_start_iteration`)} />
                  </SimpleGrid>
                  <SimpleGrid cols={2}>
                    <Switch label="Scientific notation" size="sm"
                      {...form.getInputProps(`probe_files.${idx}.scientific_notation`, { type: "checkbox" })} />
                    <NumberInput label="Output precision (digits)" step={1} min={1} max={15}
                      {...form.getInputProps(`probe_files.${idx}.output_precision`)} />
                  </SimpleGrid>

                  {/* Output variables - tristate: null=default, true=include, false=exclude */}
                  <Divider label="Output variables (checked = explicitly include)" labelPosition="center" />
                  <Text size="xs" c="dimmed">
                    Volume defaults: pressure, velocity, velocity_magnitude. Surface default: Cp.
                    Check optional variables to request them; leave unchecked to use solver defaults.
                  </Text>
                  {(() => {
                    const isVolume = pf.probe_type === "volume";
                    const varRows: Array<{ key: keyof ProbeFileOutputVars; label: string; surfaceOnly?: boolean }> = [
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
                            importProbeCSV(idx, ev.target?.result as string ?? "");
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
                  <Text size="xs" c="dimmed">CSV format: x_pos;y_pos;z_pos;description (no header)</Text>
                  {pf.points.map((pt, pidx) => (
                    <Paper key={pidx} withBorder p="xs" bg="gray.0">
                      <Group justify="space-between" mb={4}>
                        <Text size="xs" fw={500}># {pidx + 1}</Text>
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
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>

      {/* ── Target Part Names ─────────────────────────────────────────── */}'''

OLD_TARGET_HEADER = '''      {/* ── Target Part Names ─────────────────────────────────────────── */}'''
assert OLD_TARGET_HEADER in src, "Target Part Names header not found"
src = src.replace(OLD_TARGET_HEADER, PROBE_UI, 1)

FORM_FILE.write_text(src, encoding="utf-8")
print("Done — probe UI written to TemplateSettingsForm.tsx")
