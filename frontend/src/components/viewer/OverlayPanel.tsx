import { Tabs, Stack, Switch, Badge, Text, Group, Tooltip, Divider } from "@mantine/core";
import { useViewerStore } from "../../stores/viewerStore";
import type { OverlayData } from "../../api/preview";

interface OverlayPanelProps {
  overlayData: OverlayData | null;
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

// ─── TabMasterSwitch — master toggle for all items in a tab ──────────────────

function TabMasterSwitch({ visKeys }: { visKeys: string[] }) {
  const { overlayVisibility, setOverlayVisibility } = useViewerStore();
  if (visKeys.length === 0) return null;
  const allVisible = visKeys.every((k) => overlayVisibility[k] !== false);
  return (
    <Group justify="flex-end" mb={4}>
      <Switch
        size="xs"
        label={<Text size="xs" c="dimmed">All</Text>}
        checked={allVisible}
        onChange={(e) => visKeys.forEach((k) => setOverlayVisibility(k, e.currentTarget.checked))}
      />
    </Group>
  );
}

// ─── Parts tab — pattern badge groups ────────────────────────────────────────

function PartsTab({ overlayData }: { overlayData: OverlayData }) {
  const { setSearchQuery } = useViewerStore();
  const groups = overlayData.parts_groups;
  const domainParts = overlayData.domain_parts;
  const dpVisKeys = domainParts.map((dp) => `dp_${dp.name}`);

  const hasGroups = groups.length > 0;
  const hasDomainParts = domainParts.length > 0;

  if (!hasGroups && !hasDomainParts) {
    return <Text size="xs" c="dimmed">No part patterns defined in template.</Text>;
  }

  return (
    <Stack gap="sm">
      {hasGroups && (
        <>
          <Text size="xs" c="dimmed">
            Click a pattern to filter the Part List.
          </Text>
          {groups.map((g) => (
            <div key={g.label}>
              <Text size="xs" fw={600} mb={4}>
                {g.label}
                {g.matched_parts.length > 0 && (
                  <Text component="span" size="xs" c="dimmed" ml={4}>
                    ({g.matched_parts.length} parts)
                  </Text>
                )}
              </Text>
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
        </>
      )}

      {hasDomainParts && (
        <>
          {hasGroups && <Divider />}
          <Group justify="space-between" align="center">
            <Text size="xs" fw={600} c="dimmed">Domain Parts</Text>
            <TabMasterSwitch visKeys={dpVisKeys} />
          </Group>
          {domainParts.map((dp) => (
            <OverlaySwitch
              key={dp.name}
              label={dp.name}
              sub={`${dp.export_mesh ? "Belt" : "Ground patch"} | ${dp.location}`}
              visKey={`dp_${dp.name}`}
            />
          ))}
        </>
      )}
    </Stack>
  );
}

// ─── Box tab — Domain / Refinement / Porous / PV / Domain Parts ──────────────

function BoxTab({ overlayData }: { overlayData: OverlayData }) {
  const allVisKeys: string[] = [];
  if (overlayData.domain_box) allVisKeys.push("domain_box");
  overlayData.refinement_boxes.forEach((b) => allVisKeys.push(`box_${b.name}`));
  overlayData.porous_boxes.forEach((b) => allVisKeys.push(`box_${b.name}`));
  overlayData.partial_volume_boxes.forEach((b) => allVisKeys.push(`pv_${b.name}`));

  return (
    <Stack gap="sm">
      <TabMasterSwitch visKeys={allVisKeys} />

      {/* Domain bounding box */}
      {overlayData.domain_box && (
        <OverlaySwitch label="Domain bounding box" sub="Setup domain extents" visKey="domain_box" />
      )}

      {/* Refinement boxes */}
      {overlayData.refinement_boxes.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Box Refinements</Text>
          {overlayData.refinement_boxes.map((b) => (
            <OverlaySwitch
              key={b.name}
              label={b.name}
              sub={b.level != null ? `RL${b.level}` : undefined}
              visKey={`box_${b.name}`}
            />
          ))}
        </>
      )}

      {/* Porous boxes */}
      {overlayData.porous_boxes.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Part-based Boxes</Text>
          {overlayData.porous_boxes.map((b) => (
            <OverlaySwitch
              key={b.name}
              label={b.name}
              sub={b.level != null ? `RL${b.level}` : undefined}
              visKey={`box_${b.name}`}
            />
          ))}
        </>
      )}

      {/* Partial volumes */}
      {overlayData.partial_volume_boxes.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Partial Volumes</Text>
          {overlayData.partial_volume_boxes.map((b) => (
            <OverlaySwitch
              key={b.name}
              label={b.name}
              visKey={`pv_${b.name}`}
            />
          ))}
        </>
      )}

      {allVisKeys.length === 0 && (
        <Text size="xs" c="dimmed">No boxes defined in template.</Text>
      )}
    </Stack>
  );
}

// ─── Plane tab — TG + Section cuts ───────────────────────────────────────────

function PlaneTab({ overlayData }: { overlayData: OverlayData }) {
  const allVisKeys: string[] = [];
  overlayData.tg_planes.forEach((p) => allVisKeys.push(p.type));
  overlayData.section_cut_planes.forEach((p) => allVisKeys.push(`sc_${p.name}`));

  return (
    <Stack gap="sm">
      <TabMasterSwitch visKeys={allVisKeys} />

      {overlayData.tg_planes.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Turbulence Generators</Text>
          {overlayData.tg_planes.map((tg) => (
            <OverlaySwitch
              key={tg.name}
              label={tg.name}
              sub={`x = ${tg.position[0].toFixed(3)} m, w = ${tg.width.toFixed(3)}, h = ${tg.height.toFixed(4)}`}
              visKey={tg.type}
            />
          ))}
        </>
      )}

      {overlayData.section_cut_planes.length > 0 && (
        <>
          <Text size="xs" fw={600} c="dimmed">Section Cuts</Text>
          {overlayData.section_cut_planes.map((sc) => (
            <OverlaySwitch
              key={sc.name}
              label={sc.name}
              sub={`axis (${sc.normal[0]}, ${sc.normal[1]}, ${sc.normal[2]})`}
              visKey={`sc_${sc.name}`}
            />
          ))}
        </>
      )}

      {allVisKeys.length === 0 && (
        <Text size="xs" c="dimmed" mt={4}>No section cuts or TGs defined.</Text>
      )}
    </Stack>
  );
}

// ─── Point tab — RH Reference + Probe files ───────────────────────────────────

function PointTab({ overlayData }: { overlayData: OverlayData }) {
  const { rhRefVisible, setRhRefVisible } = useViewerStore();
  const rh = overlayData.ride_height_ref;
  const hasProbes = overlayData.probes.length > 0;
  const allProbeVisKeys = overlayData.probes.map((pf) => `probe_${pf.name}`);

  const zFront = rh?.reference_z_front;
  const zRear  = rh?.reference_z_rear;
  const xFront = rh?.reference_x_front;
  const xRear  = rh?.reference_x_rear;
  const hasCoords = zFront != null && zRear != null;

  return (
    <Stack gap="sm">
      {/* ── Ride Height Reference ───────────────────────────── */}
      <div>
        <Group justify="space-between" align="center" mb={6}>
          <Text size="xs" fw={600} c="dimmed">Ride Height Reference</Text>
          {rh && (
            <Switch
              size="xs"
              checked={rhRefVisible}
              onChange={(e) => setRhRefVisible(e.currentTarget.checked)}
              label={<Text size="xs" c="dimmed">Show</Text>}
            />
          )}
        </Group>

        {!rh && (
          <Text size="xs" c="dimmed">Select a template and assembly.</Text>
        )}

        {rh && (
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Mode: {rh.reference_mode === "user_input" ? "User input" : "Wheel axis (auto)"}
            </Text>

            {rh.reference_parts.length > 0 && (
              <Group gap={4} wrap="wrap">
                <Text size="xs" c="dimmed">Patterns:</Text>
                {rh.reference_parts.map((p) => (
                  <Badge key={p} size="xs" variant="light">{p}</Badge>
                ))}
              </Group>
            )}

            {hasCoords ? (
              <>
                <Group gap="xs">
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#ff4444" }} />
                  <Text size="xs">Front: ({(xFront ?? 0).toFixed(3)}, 0, {zFront!.toFixed(4)}) m</Text>
                </Group>
                <Group gap="xs">
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#4444ff" }} />
                  <Text size="xs">Rear: &nbsp;({(xRear ?? 0).toFixed(3)}, 0, {zRear!.toFixed(4)}) m</Text>
                </Group>
              </>
            ) : (
              <Text size="xs" c="dimmed">Coordinates not available — assembly not loaded.</Text>
            )}
          </Stack>
        )}
      </div>

      {/* ── Probe files ─────────────────────────────────────── */}
      <Divider />
      {hasProbes ? (
        <>
          <Group justify="space-between" align="center">
            <Text size="xs" fw={600} c="dimmed">Probe Files</Text>
            <TabMasterSwitch visKeys={allProbeVisKeys} />
          </Group>
          {overlayData.probes.map((pf) => (
            <OverlaySwitch
              key={pf.name}
              label={pf.name}
              sub={`${pf.points.length} point${pf.points.length !== 1 ? "s" : ""}`}
              visKey={`probe_${pf.name}`}
            />
          ))}
        </>
      ) : (
        <Text size="xs" c="dimmed">No probe files defined in template.</Text>
      )}
    </Stack>
  );
}

// ─── Main export ─────────────────────────────────────────────────────────────

export function OverlayPanel({ overlayData }: OverlayPanelProps) {
  if (!overlayData) {
    return (
      <Text size="xs" c="dimmed" ta="center" py="sm">
        Select a template and assembly to see overlay options.
      </Text>
    );
  }

  return (
    <Tabs defaultValue="box" variant="pills" radius="sm">
      <Tabs.List grow mb="xs">
        <Tabs.Tab value="parts" fz={10} p={4}>Parts</Tabs.Tab>
        <Tabs.Tab value="box" fz={10} p={4}>Box</Tabs.Tab>
        <Tabs.Tab value="plane" fz={10} p={4}>Plane</Tabs.Tab>
        <Tabs.Tab value="point" fz={10} p={4}>Point</Tabs.Tab>
      </Tabs.List>

      <div>
        <Tabs.Panel value="parts">
          <PartsTab overlayData={overlayData} />
        </Tabs.Panel>
        <Tabs.Panel value="box">
          <BoxTab overlayData={overlayData} />
        </Tabs.Panel>
        <Tabs.Panel value="plane">
          <PlaneTab overlayData={overlayData} />
        </Tabs.Panel>
        <Tabs.Panel value="point">
          <PointTab overlayData={overlayData} />
        </Tabs.Panel>
      </div>
    </Tabs>
  );
}
