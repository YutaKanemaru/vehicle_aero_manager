import { Tabs, Stack, Switch, Badge, Text, Group, Tooltip, ScrollArea } from "@mantine/core";
import { useViewerStore } from "../../stores/viewerStore";

interface OverlayPanelProps {
  templateSettings: Record<string, unknown> | null;
}

// ─── Typed helpers ───────────────────────────────────────────────────────────

type AnyRecord = Record<string, unknown>;

function asRecord(v: unknown): AnyRecord | undefined {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as AnyRecord) : undefined;
}
function asArray<T = unknown>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}
function asStringArray(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
}

// ─── OverlaySwitch — single row with label + optional sub-text ────────────────

function OverlaySwitch({
  label,
  sub,
  visKey,
}: {
  label: string;
  sub?: string;
  visKey: string;
}) {
  const { overlayVisibility, setOverlayVisibility } = useViewerStore();
  const checked = overlayVisibility[visKey] !== false;
  return (
    <Group gap="xs" wrap="nowrap" align="flex-start">
      <Switch
        size="xs"
        checked={checked}
        onChange={(e) => setOverlayVisibility(visKey, e.currentTarget.checked)}
        mt={sub ? 2 : 0}
      />
      <div style={{ minWidth: 0 }}>
        <Text size="xs" style={{ lineHeight: 1.3 }}>{label}</Text>
        {sub && <Text size="xs" c="dimmed" style={{ lineHeight: 1.2 }}>{sub}</Text>}
      </div>
    </Group>
  );
}

// ─── Parts tab ───────────────────────────────────────────────────────────────

function PartsTab({ ts }: { ts: AnyRecord }) {
  const { setSearchQuery } = useViewerStore();

  const setupOption = asRecord(ts.setup_option);
  const setup = asRecord(ts.setup);
  const tn = asRecord(ts.target_names);
  const meshingSetup = asRecord(asRecord(setup?.meshing)?.offset_refinement) ?? {};
  const customRefinement = asRecord(asRecord(setup?.meshing)?.custom_refinement) ?? {};
  const rhParts = asStringArray(asRecord(setupOption?.ride_height)?.reference_parts);

  // Collect sections
  type PatternGroup = { label: string; patterns: string[] };
  const groups: PatternGroup[] = [];

  // target_names groups
  const tnGroups: [string, string][] = [
    ["Wheel", "wheel"],
    ["Rim", "rim"],
    ["Baffle", "baffle"],
    ["Wind tunnel", "windtunnel"],
  ];
  for (const [label, key] of tnGroups) {
    const pats = asStringArray(tn?.[key]);
    if (pats.length > 0) groups.push({ label, patterns: pats });
  }

  // Offset refinement parts
  for (const [name, v] of Object.entries(meshingSetup)) {
    const pats = asStringArray(asRecord(v)?.parts);
    if (pats.length > 0) groups.push({ label: `Offset: ${name}`, patterns: pats });
  }

  // Custom refinement parts
  for (const [name, v] of Object.entries(customRefinement)) {
    const pats = asStringArray(asRecord(v)?.parts);
    if (pats.length > 0) groups.push({ label: `Custom: ${name}`, patterns: pats });
  }

  // Ride height reference parts
  if (rhParts.length > 0) groups.push({ label: "RH Reference", patterns: rhParts });

  if (groups.length === 0) {
    return <Text size="xs" c="dimmed">No part patterns defined in template.</Text>;
  }

  return (
    <Stack gap="sm">
      <Text size="xs" c="dimmed">
        Click a pattern to filter the Part List.
      </Text>
      {groups.map((g) => (
        <div key={g.label}>
          <Text size="xs" fw={600} mb={4}>{g.label}</Text>
          <Group gap={4} wrap="wrap">
            {g.patterns.map((p) => (
              <Tooltip key={p} label="Set as Part List filter" position="top" withArrow>
                <Badge
                  size="sm"
                  variant="light"
                  style={{ cursor: "pointer" }}
                  onClick={() => setSearchQuery(p)}
                >
                  {p}
                </Badge>
              </Tooltip>
            ))}
          </Group>
        </div>
      ))}
    </Stack>
  );
}

// ─── Box tab ─────────────────────────────────────────────────────────────────

function BoxTab({ ts }: { ts: AnyRecord }) {
  const setup = asRecord(ts.setup);
  const meshing = asRecord(asRecord(setup?.meshing));
  const boxRefinement = asRecord(meshing?.box_refinement) ?? {};
  const partBasedBox = asRecord(meshing?.part_based_box_refinement) ?? {};
  const output = asRecord(ts.output);
  const pvs = asArray<AnyRecord>(output?.partial_volumes);

  return (
    <Stack gap="sm">
      {/* Domain bounding box */}
      <OverlaySwitch label="Domain bounding box" sub="Setup domain extents" visKey="domain_box" />

      {/* Box refinements */}
      {Object.keys(boxRefinement).length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Box Refinements</Text>
          {Object.entries(boxRefinement).map(([name, v]) => {
            const br = asRecord(v);
            const level = br?.level as number | undefined;
            return (
              <OverlaySwitch
                key={name}
                label={name}
                sub={level !== undefined ? `RL${level}` : undefined}
                visKey={`box_${name}`}
              />
            );
          })}
        </>
      )}

      {/* Part-based box refinements */}
      {Object.keys(partBasedBox).length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Part-based Boxes</Text>
          {Object.entries(partBasedBox).map(([name, v]) => {
            const br = asRecord(v);
            const level = br?.level as number | undefined;
            return (
              <OverlaySwitch
                key={name}
                label={name}
                sub={level !== undefined ? `RL${level}` : undefined}
                visKey={`box_${name}`}
              />
            );
          })}
        </>
      )}

      {/* Partial volumes */}
      {pvs.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Partial Volumes</Text>
          {pvs.map((pv) => {
            const name = pv.name as string ?? "partial_volume";
            return (
              <OverlaySwitch
                key={name}
                label={name}
                sub={pv.bbox_mode as string | undefined}
                visKey={`pv_${name}`}
              />
            );
          })}
        </>
      )}

      {Object.keys(boxRefinement).length === 0 && Object.keys(partBasedBox).length === 0 && pvs.length === 0 && (
        <Text size="xs" c="dimmed">No boxes defined in template.</Text>
      )}
    </Stack>
  );
}

// ─── Plane tab ────────────────────────────────────────────────────────────────

function PlaneTab({ ts }: { ts: AnyRecord }) {
  const output = asRecord(ts.output);
  const scs = asArray<AnyRecord>(output?.section_cuts);

  // Ground height config
  const setupOption = asRecord(ts.setup_option);
  const gc = asRecord(asRecord(setupOption?.boundary_condition)?.ground);
  const groundMode = gc?.ground_height_mode as string | undefined;
  const groundOffset = gc?.ground_height_offset_from_geom_zMin as number | undefined;
  const groundAbsolute = gc?.ground_height_absolute as number | undefined;
  let groundSub: string;
  if (groundMode === "absolute") {
    groundSub = `absolute z = ${(groundAbsolute ?? 0).toFixed(3)} m`;
  } else if (groundOffset && groundOffset !== 0) {
    groundSub = `from geometry z_min + ${groundOffset.toFixed(3)} m`;
  } else {
    groundSub = "from geometry z_min";
  }

  // TG config
  const tgCfg = asRecord(asRecord(setupOption?.boundary_condition)?.turbulence_generator);
  const enableGroundTg = tgCfg?.enable_ground_tg === true;
  const enableBodyTg = tgCfg?.enable_body_tg === true;
  const blSuction = asRecord(gc?.bl_suction);
  const noSlipXminPos = blSuction?.no_slip_xmin_pos;
  const tgGroundSub = noSlipXminPos != null
    ? `x_pos = ${((noSlipXminPos as number) - 0.01).toFixed(3)} m`
    : "x_pos = vehicle x_min − 0.01 m (auto)";
  const simParam = asRecord(ts.simulation_parameter);
  const coarsest = (simParam?.coarsest_voxel_size as number) ?? 0.192;
  const h_rl6 = coarsest / 8;

  return (
    <Stack gap="sm">
      <OverlaySwitch label="Ground plane" sub={groundSub} visKey="ground_plane" />

      {(enableGroundTg || enableBodyTg) && (
        <>
          <Text size="xs" fw={600} c="dimmed">Turbulence Generators</Text>
          {enableGroundTg && (
            <OverlaySwitch
              label="TG Ground"
              sub={`${tgGroundSub}, h = ${h_rl6.toFixed(4)} m`}
              visKey="tg_ground"
            />
          )}
          {enableBodyTg && (
            <OverlaySwitch
              label="TG Body"
              sub="y ±45%, z 10–65% of height"
              visKey="tg_body"
            />
          )}
        </>
      )}

      {scs.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Section Cuts</Text>
          {scs.map((sc) => {
            const name = sc.name as string ?? "section_cut";
            const ax = sc.axis_x as number | undefined;
            const ay = sc.axis_y as number | undefined;
            const az = sc.axis_z as number | undefined;
            const sub = ax !== undefined ? `axis (${ax}, ${ay}, ${az})` : undefined;
            return (
              <OverlaySwitch key={name} label={name} sub={sub} visKey={`sc_${name}`} />
            );
          })}
        </>
      )}

      {scs.length === 0 && !enableGroundTg && !enableBodyTg && (
        <Text size="xs" c="dimmed" mt={4}>No section cuts or TGs defined in template.</Text>
      )}
    </Stack>
  );
}

// ─── Probe tab ────────────────────────────────────────────────────────────────

function ProbeTab({ ts }: { ts: AnyRecord }) {
  const output = asRecord(ts.output);
  const probeFiles = asArray<AnyRecord>(output?.probe_files);

  if (probeFiles.length === 0) {
    return <Text size="xs" c="dimmed">No probe files defined in template.</Text>;
  }

  return (
    <Stack gap="sm">
      {probeFiles.map((pf) => {
        const name = pf.name as string ?? "probe";
        const pts = asArray(pf.points);
        return (
          <OverlaySwitch
            key={name}
            label={name}
            sub={`${pts.length} point${pts.length !== 1 ? "s" : ""}`}
            visKey={`probe_${name}`}
          />
        );
      })}
    </Stack>
  );
}

// ─── Main export ─────────────────────────────────────────────────────────────

export function OverlayPanel({ templateSettings }: OverlayPanelProps) {
  if (!templateSettings) {
    return (
      <Text size="xs" c="dimmed" ta="center" py="sm">
        Select a template to see overlay options.
      </Text>
    );
  }

  return (
    <Tabs defaultValue="box" variant="pills" radius="sm">
      <Tabs.List grow mb="xs">
        <Tabs.Tab value="parts" fz={10} p={4}>Parts</Tabs.Tab>
        <Tabs.Tab value="box" fz={10} p={4}>Box</Tabs.Tab>
        <Tabs.Tab value="plane" fz={10} p={4}>Plane</Tabs.Tab>
        <Tabs.Tab value="probe" fz={10} p={4}>Probe</Tabs.Tab>
      </Tabs.List>

      <ScrollArea style={{ maxHeight: 280 }} type="auto">
        <Tabs.Panel value="parts">
          <PartsTab ts={templateSettings} />
        </Tabs.Panel>
        <Tabs.Panel value="box">
          <BoxTab ts={templateSettings} />
        </Tabs.Panel>
        <Tabs.Panel value="plane">
          <PlaneTab ts={templateSettings} />
        </Tabs.Panel>
        <Tabs.Panel value="probe">
          <ProbeTab ts={templateSettings} />
        </Tabs.Panel>
      </ScrollArea>
    </Tabs>
  );
}
