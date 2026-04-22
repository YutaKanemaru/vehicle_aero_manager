import { useState, useMemo } from "react";
import {
  Stack,
  Select,
  Switch,
  Divider,
  Title,
  Paper,
  ScrollArea,
  Text,
  Button,
  Group,
  ActionIcon,
  Tooltip,
  SegmentedControl,
} from "@mantine/core";
import { IconSun, IconMoon, IconCamera, IconPackage, IconPlus, IconPencil } from "@tabler/icons-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { assembliesApi, type AssemblyResponse, type GeometryResponse } from "../../api/geometries";
import { templatesApi, type TemplateResponse } from "../../api/templates";
import { useViewerStore } from "../../stores/viewerStore";
import { SceneCanvas } from "./SceneCanvas";
import { PartListPanel } from "./PartListPanel";
import { AssemblyGeometriesDrawer } from "../assemblies/AssemblyGeometriesDrawer";
import { CreateCaseFromBuilderModal } from "../cases/CreateCaseFromBuilderModal";
import { TemplateVersionEditModal } from "../templates/TemplateVersionEditModal";
import { OverlayPanel } from "./OverlayPanel";

// ─── Left panel ──────────────────────────────────────────────────────────────

function ControlPanel({
  // geometries kept for potential future use
  geometries: _geometries,
  templateSettings,
}: {
  geometries: GeometryResponse[];
  templateSettings: Record<string, unknown> | null;
}) {
  const {
    selectedAssemblyId, setSelectedAssemblyId,
    selectedTemplateId, setSelectedTemplateId,
  } = useViewerStore();
  const queryClient = useQueryClient();

  // Assembly builder drawer state
  const [assemblyBuilderOpen, setAssemblyBuilderOpen] = useState(false);
  const [createCaseOpen, setCreateCaseOpen] = useState(false);
  const [editTemplateOpen, setEditTemplateOpen] = useState(false);

  function handleBuilderClose() {
    setAssemblyBuilderOpen(false);
    // Refresh both the flat assemblies list and the full assembly detail
    queryClient.invalidateQueries({ queryKey: ["assemblies"] });
    queryClient.invalidateQueries({ queryKey: ["assembly", selectedAssemblyId] });
  }

  const { data: assemblies = [] } = useQuery<AssemblyResponse[]>({
    queryKey: ["assemblies"],
    queryFn: () => assembliesApi.list(),
  });

  const { data: templates = [] } = useQuery<TemplateResponse[]>({
    queryKey: ["templates"],
    queryFn: () => templatesApi.list(),
  });

  const { data: templateDetail } = useQuery({
    queryKey: ["templates", selectedTemplateId],
    queryFn: () => templatesApi.get(selectedTemplateId!),
    enabled: !!selectedTemplateId,
  });

  const { data: templateVersions } = useQuery({
    queryKey: ["templates", selectedTemplateId, "versions"],
    queryFn: () => templatesApi.listVersions(selectedTemplateId!),
    enabled: !!selectedTemplateId,
  });

  const activeVersion = useMemo(() => {
    if (!templateVersions || templateVersions.length === 0) return null;
    return templateVersions.find((v) => v.is_active) ?? templateVersions[templateVersions.length - 1];
  }, [templateVersions]);

  const assemblyOptions = assemblies.map((a) => ({ value: a.id, label: a.name }));
  const templateOptions = [
    { value: "", label: "— No template overlay —" },
    ...templates.map((t) => ({ value: t.id, label: t.name })),
  ];

  return (
    <Stack gap="sm" style={{ height: "100%" }}>
      <Title order={5}>Template Builder</Title>

      {/* Assembly selector + Launch Assembly Builder button */}
      <Group gap="xs" align="flex-end" wrap="nowrap">
        <Select
          label="Assembly"
          placeholder="Select assembly..."
          data={assemblyOptions}
          value={selectedAssemblyId}
          onChange={(v) => setSelectedAssemblyId(v)}
          clearable
          size="sm"
          style={{ flex: 1 }}
        />
        <Tooltip label="Launch Assembly Builder" position="right">
          <ActionIcon
            size="md"
            variant="light"
            color="teal"
            disabled={!selectedAssemblyId}
            onClick={() => setAssemblyBuilderOpen(true)}
            mb={2}
          >
            <IconPackage size={15} />
          </ActionIcon>
        </Tooltip>
      </Group>

      {/* Template selector + Edit Template button */}
      <Group gap="xs" align="flex-end" wrap="nowrap">
        <Select
          label="Template overlay"
          placeholder="Select template..."
          data={templateOptions}
          value={selectedTemplateId ?? ""}
          onChange={(v) => setSelectedTemplateId(v || null)}
          clearable
          size="sm"
          style={{ flex: 1 }}
        />
        <Tooltip label="Edit template settings" position="right">
          <ActionIcon
            size="md"
            variant="light"
            color="violet"
            disabled={!selectedTemplateId || !activeVersion || !templateDetail}
            onClick={() => setEditTemplateOpen(true)}
            mb={2}
          >
            <IconPencil size={15} />
          </ActionIcon>
        </Tooltip>
      </Group>

      {/* Create Case button — enabled only when both assembly + template are selected */}
      <Button
        size="sm"
        leftSection={<IconPlus size={14} />}
        disabled={!selectedAssemblyId || !selectedTemplateId}
        variant="filled"
        color="blue"
        onClick={() => setCreateCaseOpen(true)}
      >
        Create Case
      </Button>

      <Divider label="Overlays" labelPosition="left" />
      <OverlayPanel templateSettings={templateSettings} />

      <AssemblyGeometriesDrawer
        assemblyId={selectedAssemblyId}
        opened={assemblyBuilderOpen}
        onClose={handleBuilderClose}
      />

      {selectedAssemblyId && selectedTemplateId && (
        <CreateCaseFromBuilderModal
          opened={createCaseOpen}
          onClose={() => setCreateCaseOpen(false)}
          assemblyId={selectedAssemblyId}
          templateId={selectedTemplateId}
        />
      )}

      {editTemplateOpen && templateDetail && activeVersion && (
        <TemplateVersionEditModal
          opened={editTemplateOpen}
          onClose={() => setEditTemplateOpen(false)}
          template={templateDetail}
          version={activeVersion}
        />
      )}
    </Stack>
  );
}

// ─── Floating camera controls (bottom-right of 3D view) ─────────────────────

function CameraOverlay() {
  const { setCameraPreset, viewerTheme, setViewerTheme } = useViewerStore();
  return (
    <div
      style={{
        position: "absolute",
        bottom: 8,
        right: 4,
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        gap: 4,
        alignItems: "flex-end",
        pointerEvents: "all",
      }}
    >
      <Group gap={4} wrap="wrap" justify="flex-end">
        {(["iso", "front", "rear", "side", "top"] as const).map((preset) => (
          <Tooltip key={preset} label={`${preset} view`}>
            <Button
              size="xs"
              variant="light"
              style={{ background: "rgba(0,0,0,0.55)", borderColor: "rgba(255,255,255,0.15)" }}
              leftSection={<IconCamera size={11} />}
              onClick={() => setCameraPreset(preset)}
            >
              {preset}
            </Button>
          </Tooltip>
        ))}
      </Group>
      <Tooltip label="Toggle background">
        <ActionIcon
          size="sm"
          variant="light"
          style={{ background: "rgba(0,0,0,0.55)", borderColor: "rgba(255,255,255,0.15)" }}
          onClick={() => setViewerTheme(viewerTheme === "dark" ? "light" : "dark")}
        >
          {viewerTheme === "dark" ? <IconSun size={14} /> : <IconMoon size={14} />}
        </ActionIcon>
      </Tooltip>
    </div>
  );
}

// ─── Floating viewer toolbar (Persp/Ortho + FlatShading + Edges) ─────────────

function ViewerToolbar() {
  const { cameraProjection, setCameraProjection, flatShading, setFlatShading, showEdges, setShowEdges } = useViewerStore();
  return (
    <div
      style={{
        position: "absolute",
        top: 8,
        right: 8,
        zIndex: 10,
        display: "flex",
        gap: 8,
        alignItems: "center",
        background: "rgba(0,0,0,0.6)",
        borderRadius: 6,
        padding: "4px 10px",
        pointerEvents: "all",
      }}
    >
      <SegmentedControl
        size="xs"
        value={cameraProjection}
        onChange={(v) => setCameraProjection(v as "perspective" | "orthographic")}
        data={[
          { label: "Persp", value: "perspective" },
          { label: "Ortho", value: "orthographic" },
        ]}
      />
      <Switch
        size="xs"
        label="Flat"
        checked={flatShading}
        onChange={(e) => setFlatShading(e.currentTarget.checked)}
      />
      <Switch
        size="xs"
        label="Edges"
        checked={showEdges}
        onChange={(e) => setShowEdges(e.currentTarget.checked)}
      />
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export function TemplateBuilderPage() {
  const {
    selectedAssemblyId,
    selectedTemplateId,
  } = useViewerStore();
  const { ratio } = useViewerStore();

  const { data: assemblies = [] } = useQuery<AssemblyResponse[]>({
    queryKey: ["assemblies"],
    queryFn: () => assembliesApi.list(),
  });

  const { data: templateVersions } = useQuery({
    queryKey: ["templates", selectedTemplateId, "versions"],
    queryFn: () =>
      selectedTemplateId ? templatesApi.listVersions(selectedTemplateId) : Promise.resolve([]),
    enabled: !!selectedTemplateId,
  });

  const selectedAssembly = assemblies.find((a) => a.id === selectedAssemblyId);
  const geometries: GeometryResponse[] = selectedAssembly?.geometries ?? [];

  // 車両全体のbboxを全ジオメトリのunionで計算
  const vehicleBbox = useMemo(() => {
    if (geometries.length === 0) return null;
    let xMin = Infinity, xMax = -Infinity;
    let yMin = Infinity, yMax = -Infinity;
    let zMin = Infinity, zMax = -Infinity;
    for (const g of geometries) {
      const ar = g.analysis_result as { vehicle_bbox?: Record<string, number> } | null;
      if (!ar?.vehicle_bbox) continue;
      const b = ar.vehicle_bbox;
      xMin = Math.min(xMin, b.x_min); xMax = Math.max(xMax, b.x_max);
      yMin = Math.min(yMin, b.y_min); yMax = Math.max(yMax, b.y_max);
      zMin = Math.min(zMin, b.z_min); zMax = Math.max(zMax, b.z_max);
    }
    if (xMin === Infinity) return null;
    return { x_min: xMin, x_max: xMax, y_min: yMin, y_max: yMax, z_min: zMin, z_max: zMax };
  }, [geometries]);

  // アクティブバージョンのsettingsを取得
  const activeVersion = useMemo(() => {
    if (!templateVersions || templateVersions.length === 0) return null;
    return templateVersions.find((v) => v.is_active) ?? templateVersions[templateVersions.length - 1];
  }, [templateVersions]);

  const templateSettings = activeVersion?.settings ?? null;

  // part_info: 全ジオメトリの analysis_result.part_info をマージ
  const partInfo = useMemo(() => {
    const merged: Record<string, unknown> = {};
    for (const g of geometries) {
      const ar = g.analysis_result as { part_info?: Record<string, unknown> } | null;
      if (!ar?.part_info) continue;
      Object.assign(merged, ar.part_info);
    }
    return Object.keys(merged).length > 0 ? merged : null;
  }, [geometries]);

  // All parts across all geometries in the assembly
  const allParts = useMemo(() => {
    return geometries.flatMap(
      (g) => (g.analysis_result as { parts?: string[] } | null)?.parts ?? []
    );
  }, [geometries]);

  return (
    <div style={{ display: "flex", height: "calc(100vh - 80px)", gap: 8 }}>
      {/* Left panel: 275px — Controls */}
      <Paper
        withBorder
        p="sm"
        style={{ width: 275, flexShrink: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}
      >
        <ScrollArea style={{ flex: 1 }} type="auto">
          <ControlPanel geometries={geometries} templateSettings={templateSettings as Record<string, unknown> | null} />
        </ScrollArea>
      </Paper>

      {/* Middle panel: 255px — Part list */}
      <Paper
        withBorder
        p="xs"
        style={{ width: 255, flexShrink: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}
      >
        <Text size="xs" fw={600} mb={4}>Parts</Text>
        <PartListPanel parts={allParts} partInfo={partInfo} />
      </Paper>

      {/* Right panel: 3D canvas */}
      <Paper
        withBorder
        style={{ flex: 1, overflow: "hidden", position: "relative" }}
      >
        <ViewerToolbar />
        <CameraOverlay />
        <SceneCanvas
          geometries={geometries}
          ratio={ratio}
          templateSettings={templateSettings as Record<string, unknown> | null}
          vehicleBbox={vehicleBbox}
          partInfo={partInfo}
        />
      </Paper>
    </div>
  );
}
