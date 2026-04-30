/**
 * RunViewer — 3D viewer for a ready Run, reusing Template Builder components.
 *
 * Layout: 275px ControlPanel | 255px PartListPanel | flex-1 SceneCanvas
 *
 * Overlay data comes from `GET /cases/{caseId}/runs/{runId}/overlay`
 * which parses the Run's generated XML → OverlayData.
 */
import { useMemo } from "react";
import {
  Stack,
  Text,
  Group,
  Switch,
  Divider,
  ScrollArea,
  SegmentedControl,
  ActionIcon,
  Tooltip,
} from "@mantine/core";
import {
  IconSun,
  IconMoon,
  IconAxisX,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import {
  runsApi,
  type RunResponse,
} from "../../api/configurations";
import { assembliesApi, geometriesApi, type GeometryResponse } from "../../api/geometries";
import { SceneCanvas } from "../viewer/SceneCanvas";
import { PartListPanel } from "../viewer/PartListPanel";
import { OverlayPanel } from "../viewer/OverlayPanel";
import { useViewerStore } from "../../stores/viewerStore";

interface RunViewerProps {
  caseId: string;
  assemblyId: string;
  run: RunResponse;
}

// Camera preset buttons
const CAMERA_PRESETS = [
  { value: "iso", label: "Iso" },
  { value: "front", label: "Front" },
  { value: "rear", label: "Rear" },
  { value: "side", label: "Side" },
  { value: "top", label: "Top" },
];

export function RunViewer({ caseId, assemblyId, run }: RunViewerProps) {
  const ratio = useViewerStore((s) => s.ratio);
  const cameraProjection = useViewerStore((s) => s.cameraProjection);
  const setCameraProjection = useViewerStore((s) => s.setCameraProjection);
  const flatShading = useViewerStore((s) => s.flatShading);
  const setFlatShading = useViewerStore((s) => s.setFlatShading);
  const showEdges = useViewerStore((s) => s.showEdges);
  const setShowEdges = useViewerStore((s) => s.setShowEdges);
  const setCameraPreset = useViewerStore((s) => s.setCameraPreset);
  const viewerTheme = useViewerStore((s) => s.viewerTheme);
  const setViewerTheme = useViewerStore((s) => s.setViewerTheme);
  const showOriginAxes = useViewerStore((s) => s.showOriginAxes);
  const setShowOriginAxes = useViewerStore((s) => s.setShowOriginAxes);
  const overlaysAllVisible = useViewerStore((s) => s.overlaysAllVisible);
  const setOverlaysAllVisible = useViewerStore((s) => s.setOverlaysAllVisible);

  // Fetch assembly details for geometries
  const { data: assembly } = useQuery({
    queryKey: ["assembly", assemblyId],
    queryFn: () => assembliesApi.get(assemblyId),
    enabled: !!assemblyId,
  });

  // Fetch override geometry when transform is applied and ready
  const { data: overrideGeometry } = useQuery({
    queryKey: ["geometry", run.geometry_override_id],
    queryFn: () => geometriesApi.get(run.geometry_override_id!),
    enabled: !!run.geometry_override_id && run.geometry_override_status === "ready",
  });

  const useOverride = !!run.geometry_override_id && run.geometry_override_status === "ready";
  const geometries: GeometryResponse[] = useOverride
    ? (overrideGeometry ? [overrideGeometry] : [])
    : (assembly?.geometries ?? []);

  // Fetch overlay data from generated XML
  const { data: overlayData } = useQuery({
    queryKey: ["runs", run.id, "overlay"],
    queryFn: () => runsApi.getOverlayData(caseId, run.id),
    enabled: run.status === "ready" && !!run.xml_path,
  });

  // Merge part info from all geometries
  const { allParts, partInfo, vehicleBbox } = useMemo(() => {
    const parts: string[] = [];
    const info: Record<string, unknown> = {};
    const bboxes: Array<{ x_min: number; x_max: number; y_min: number; y_max: number; z_min: number; z_max: number }> = [];

    for (const g of geometries) {
      const ar = g.analysis_result;
      if (ar && typeof ar === "object") {
        const a = ar as Record<string, unknown>;
        if (Array.isArray(a.parts)) parts.push(...(a.parts as string[]));
        if (a.part_info && typeof a.part_info === "object") Object.assign(info, a.part_info);
        if (a.vehicle_bbox && typeof a.vehicle_bbox === "object") bboxes.push(a.vehicle_bbox as typeof bboxes[number]);
      }
    }

    let vbbox: typeof bboxes[number] | null = null;
    if (bboxes.length > 0) {
      vbbox = {
        x_min: Math.min(...bboxes.map((b) => b.x_min)),
        x_max: Math.max(...bboxes.map((b) => b.x_max)),
        y_min: Math.min(...bboxes.map((b) => b.y_min)),
        y_max: Math.max(...bboxes.map((b) => b.y_max)),
        z_min: Math.min(...bboxes.map((b) => b.z_min)),
        z_max: Math.max(...bboxes.map((b) => b.z_max)),
      };
    }

    return { allParts: parts, partInfo: info, vehicleBbox: vbbox };
  }, [geometries]);

  if (run.status !== "ready") {
    return (
      <Text c="dimmed" size="sm" p="md">
        Select a ready run to view its 3D setup.
      </Text>
    );
  }

  return (
    <div style={{ display: "flex", height: "100%", minHeight: 500 }}>
      {/* Left: Control Panel */}
      <div style={{ width: 275, borderRight: "1px solid var(--mantine-color-default-border)", display: "flex", flexDirection: "column" }}>
        <ScrollArea style={{ flex: 1 }} p="xs">
          <Stack gap="sm">
            {/* Overlays master */}
            <Group justify="space-between">
              <Text size="sm" fw={600}>Overlays</Text>
              <Switch
                size="xs"
                checked={overlaysAllVisible}
                onChange={(e) => setOverlaysAllVisible(e.currentTarget.checked)}
                label="All"
              />
            </Group>
            <Divider />
            <OverlayPanel overlayData={overlayData ?? null} />
          </Stack>
        </ScrollArea>
      </div>

      {/* Middle: Part List */}
      <div style={{ width: 255, borderRight: "1px solid var(--mantine-color-default-border)", display: "flex", flexDirection: "column", padding: "8px 8px 0 8px" }}>
        <Text size="xs" fw={600} mb={4}>Parts</Text>
        <PartListPanel parts={allParts} partInfo={partInfo} />
      </div>

      {/* Right: 3D Canvas */}
      <div style={{ flex: 1, position: "relative" }}>
        <SceneCanvas
          geometries={geometries}
          ratio={ratio}
          overlayData={overlayData}
          vehicleBbox={vehicleBbox}
          partInfo={partInfo}
        />

        {/* Viewer Toolbar (top-right) */}
        <div style={{ position: "absolute", top: 8, right: 8, zIndex: 10, display: "flex", gap: 8, alignItems: "center", background: "rgba(0,0,0,0.5)", padding: "4px 8px", borderRadius: 6 }}>
          <SegmentedControl
            size="xs"
            data={[
              { label: "Persp", value: "perspective" },
              { label: "Ortho", value: "orthographic" },
            ]}
            value={cameraProjection}
            onChange={(v) => setCameraProjection(v as "perspective" | "orthographic")}
          />
          <Switch
            size="xs"
            label="Flat"
            checked={flatShading}
            onChange={(e) => setFlatShading(e.currentTarget.checked)}
            styles={{ label: { color: "white" } }}
          />
          <Switch
            size="xs"
            label="Edges"
            checked={showEdges}
            onChange={(e) => setShowEdges(e.currentTarget.checked)}
            styles={{ label: { color: "white" } }}
          />
        </div>

        {/* Camera Overlay (bottom-right) */}
        <div style={{ position: "absolute", bottom: 8, right: 4, zIndex: 10, display: "flex", gap: 4, alignItems: "center", background: "rgba(0,0,0,0.5)", padding: "4px 6px", borderRadius: 6 }}>
          {CAMERA_PRESETS.map((p) => (
            <Tooltip key={p.value} label={p.label}>
              <ActionIcon
                size="xs"
                variant="subtle"
                color="gray"
                onClick={() => setCameraPreset(p.value)}
              >
                <Text size="xs" c="white">{p.label[0]}</Text>
              </ActionIcon>
            </Tooltip>
          ))}
          <Tooltip label="Toggle theme">
            <ActionIcon
              size="xs"
              variant="subtle"
              onClick={() => setViewerTheme(viewerTheme === "dark" ? "light" : "dark")}
            >
              {viewerTheme === "dark" ? <IconSun size={12} color="white" /> : <IconMoon size={12} color="white" />}
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Origin axes">
            <ActionIcon
              size="xs"
              variant={showOriginAxes ? "filled" : "subtle"}
              color={showOriginAxes ? "blue" : "gray"}
              onClick={() => setShowOriginAxes(!showOriginAxes)}
            >
              <IconAxisX size={12} color="white" />
            </ActionIcon>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
