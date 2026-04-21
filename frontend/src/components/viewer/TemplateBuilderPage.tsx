import { useEffect, useMemo } from "react";
import {
  Stack,
  Select,
  Switch,
  Divider,
  Title,
  Paper,
  ScrollArea,
  Text,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { assembliesApi, type AssemblyResponse, type GeometryResponse } from "../../api/geometries";
import { templatesApi, type TemplateResponse } from "../../api/templates";
import { casesApi, runsApi, type CaseResponse, type RunResponse } from "../../api/configurations";
import { useViewerStore } from "../../stores/viewerStore";
import { SceneCanvas } from "./SceneCanvas";
import { PartListPanel } from "./PartListPanel";

// ─── Left panel ──────────────────────────────────────────────────────────────

function ControlPanel() {
  const {
    selectedAssemblyId, setSelectedAssemblyId,
    selectedTemplateId, setSelectedTemplateId,
    selectedCaseId, setSelectedCaseId,
    selectedRunId, setSelectedRunId,
    axesGlbUrl, setAxesGlbUrl,
    overlays, setOverlay,
  } = useViewerStore();

  const { data: assemblies = [] } = useQuery<AssemblyResponse[]>({
    queryKey: ["assemblies"],
    queryFn: () => assembliesApi.list(),
  });

  const { data: templates = [] } = useQuery<TemplateResponse[]>({
    queryKey: ["templates"],
    queryFn: () => templatesApi.list(),
  });

  const { data: allCases = [] } = useQuery<CaseResponse[]>({
    queryKey: ["cases"],
    queryFn: () => casesApi.list(),
  });

  const { data: runs = [] } = useQuery<RunResponse[]>({
    queryKey: ["runs", selectedCaseId],
    queryFn: () => runsApi.list(selectedCaseId!),
    enabled: !!selectedCaseId,
  });

  // Filter cases to those that match the selected assembly
  const filteredCases = useMemo(
    () => allCases.filter((c) => c.assembly_id === selectedAssemblyId),
    [allCases, selectedAssemblyId]
  );
  // Only show runs that are ready (XML generated)
  const readyRuns = useMemo(
    () => runs.filter((r) => r.status === "ready"),
    [runs]
  );

  const assemblyOptions = assemblies.map((a) => ({ value: a.id, label: a.name }));
  const templateOptions = [
    { value: "", label: "— No template overlay —" },
    ...templates.map((t) => ({ value: t.id, label: t.name })),
  ];
  const caseOptions = filteredCases.map((c) => ({ value: c.id, label: c.name }));
  const runOptions  = readyRuns.map((r) => ({ value: r.id, label: r.name }));

  // Clear case / run selection when assembly changes
  useEffect(() => {
    setSelectedCaseId(null);
    setSelectedRunId(null);
  }, [selectedAssemblyId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch (or revoke) axes GLB when run or wheelAxes toggle changes
  useEffect(() => {
    // Revoke previous blob URL
    if (axesGlbUrl) {
      URL.revokeObjectURL(axesGlbUrl);
      setAxesGlbUrl(null);
    }

    if (!selectedCaseId || !selectedRunId || !overlays.wheelAxes) return;

    let cancelled = false;
    runsApi.getAxesGlbUrl(selectedCaseId, selectedRunId)
      .then((url) => {
        if (!cancelled) setAxesGlbUrl(url);
      })
      .catch((err) => {
        console.warn("Axes GLB fetch failed:", err);
      });

    return () => { cancelled = true; };
  }, [selectedCaseId, selectedRunId, overlays.wheelAxes]); // eslint-disable-line react-hooks/exhaustive-deps

  // 選択中アセンブリのジオメトリ一覧から全パーツ名を収集
  const selectedAssembly = assemblies.find((a) => a.id === selectedAssemblyId);
  const allParts = useMemo(() => {
    if (!selectedAssembly) return [];
    return selectedAssembly.geometries.flatMap(
      (g) => (g.analysis_result as { parts?: string[] } | null)?.parts ?? []
    );
  }, [selectedAssembly]);

  return (
    <Stack gap="sm" style={{ height: "100%" }}>
      <Title order={5}>Template Builder</Title>

      <Select
        label="Assembly"
        placeholder="Select assembly..."
        data={assemblyOptions}
        value={selectedAssemblyId}
        onChange={(v) => setSelectedAssemblyId(v)}
        clearable
        size="sm"
      />

      <Select
        label="Template overlay"
        placeholder="Select template..."
        data={templateOptions}
        value={selectedTemplateId ?? ""}
        onChange={(v) => setSelectedTemplateId(v || null)}
        size="sm"
      />

      <Divider label="Axis Visualisation (Run)" labelPosition="left" />

      <Select
        label="Case"
        placeholder={selectedAssemblyId ? "Select case..." : "Select assembly first"}
        data={caseOptions}
        value={selectedCaseId}
        onChange={(v) => { setSelectedCaseId(v); setSelectedRunId(null); }}
        disabled={!selectedAssemblyId || caseOptions.length === 0}
        clearable
        size="sm"
      />
      {selectedAssemblyId && selectedCaseId && readyRuns.length === 0 && (
        <Text size="xs" c="dimmed">No ready runs in this case</Text>
      )}

      <Select
        label="Run"
        placeholder="Select run..."
        data={runOptions}
        value={selectedRunId}
        onChange={(v) => setSelectedRunId(v)}
        disabled={!selectedCaseId || runOptions.length === 0}
        clearable
        size="sm"
      />

      <Divider label="Overlays" labelPosition="left" />

      <Stack gap={6}>
        <Switch
          size="xs"
          label="Domain bounding box"
          checked={overlays.domainBox}
          onChange={(e) => setOverlay("domainBox", e.currentTarget.checked)}
        />
        <Switch
          size="xs"
          label="Refinement boxes"
          checked={overlays.refinementBoxes}
          onChange={(e) => setOverlay("refinementBoxes", e.currentTarget.checked)}
        />
        <Switch
          size="xs"
          label="Wheel / porous axes"
          checked={overlays.wheelAxes}
          onChange={(e) => setOverlay("wheelAxes", e.currentTarget.checked)}
          disabled={!selectedRunId}
        />
        <Switch
          size="xs"
          label="Ground plane"
          checked={overlays.groundPlane}
          onChange={(e) => setOverlay("groundPlane", e.currentTarget.checked)}
        />
      </Stack>

      <Divider label="Parts" labelPosition="left" />

      <div style={{ flex: 1, overflow: "hidden" }}>
        <PartListPanel parts={allParts} />
      </div>
    </Stack>
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
    queryKey: ["template-versions", selectedTemplateId],
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

  return (
    <div style={{ display: "flex", height: "calc(100vh - 80px)", gap: 8 }}>
      {/* Left panel: 300px fixed */}
      <Paper
        withBorder
        p="sm"
        style={{ width: 300, flexShrink: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}
      >
        <ScrollArea style={{ flex: 1 }} type="auto">
          <ControlPanel />
        </ScrollArea>
      </Paper>

      {/* Right panel: 3D canvas */}
      <Paper
        withBorder
        style={{ flex: 1, overflow: "hidden", position: "relative" }}
      >
        <SceneCanvas
          geometries={geometries}
          ratio={ratio}
          templateSettings={templateSettings as Record<string, unknown> | null}
          vehicleBbox={vehicleBbox}
        />
      </Paper>
    </div>
  );
}
