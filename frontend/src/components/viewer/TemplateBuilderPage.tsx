import { useEffect, useMemo, useState } from "react";
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
  Badge,
  Table,
} from "@mantine/core";
import { IconArrowDown } from "@tabler/icons-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { assembliesApi, type AssemblyResponse, type GeometryResponse } from "../../api/geometries";
import { templatesApi, type TemplateResponse } from "../../api/templates";
import { casesApi, runsApi, type CaseResponse, type RunResponse, mapsApi, conditionsApi, type ConditionResponse } from "../../api/configurations";
import { transformApi, systemsApi } from "../../api/systems";
import { useViewerStore } from "../../stores/viewerStore";
import { useJobsStore } from "../../stores/jobs";
import { SceneCanvas } from "./SceneCanvas";
import { PartListPanel } from "./PartListPanel";

// ─── Left panel ──────────────────────────────────────────────────────────────

function ControlPanel({ geometries }: { geometries: GeometryResponse[] }) {
  const {
    selectedAssemblyId, setSelectedAssemblyId,
    selectedTemplateId, setSelectedTemplateId,
    selectedCaseId, setSelectedCaseId,
    selectedRunId, setSelectedRunId,
    axesGlbUrl, setAxesGlbUrl,
    overlays, setOverlay,
    selectedConditionMapId, setSelectedConditionMapId,
    selectedConditionId, setSelectedConditionId,
    landmarksGlbUrl, setLandmarksGlbUrl,
  } = useViewerStore();
  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);

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

  // ── Condition map / condition queries ─────────────────────────────────────
  const { data: conditionMaps = [] } = useQuery({
    queryKey: ["maps"],
    queryFn: mapsApi.list,
  });
  const { data: conditions = [] } = useQuery<ConditionResponse[]>({
    queryKey: ["conditions", selectedConditionMapId],
    queryFn: () => conditionsApi.list(selectedConditionMapId!),
    enabled: !!selectedConditionMapId,
  });
  const selectedCondition = conditions.find((c) => c.id === selectedConditionId) ?? null;

  // Local state for geometry-to-transform selection and last result
  const [selectedGeometryId, setSelectedGeometryId] = useState<string | null>(null);
  const [transformResult, setTransformResult] = useState<{
    front_error: number; rear_error: number; system_id: string;
  } | null>(null);

  const transformMutation = useMutation({
    mutationFn: () => {
      if (!selectedGeometryId || !selectedCondition) throw new Error("Select geometry and condition first");
      const geom = geometries.find((g) => g.id === selectedGeometryId);
      const name = `${geom?.name ?? "geometry"}_${selectedCondition.name}`;
      return transformApi.transform(selectedGeometryId, {
        name,
        condition_id: selectedCondition.id,
        ride_height: selectedCondition.ride_height ?? { enabled: false },
        yaw_angle_deg: selectedCondition.yaw_angle,
        yaw_config: selectedCondition.yaw_config ?? { center_mode: "wheel_center", center_x: 0, center_y: 0 },
      });
    },
    onSuccess: (result) => {
      // Add the resulting geometry to the jobs tracker
      addJob(result.geometry_id, result.geometry_name, "stl_analysis");
      updateJob(result.geometry_id, "analyzing");
      // Extract verification from transform_snapshot
      const snap = result.transform_snapshot as Record<string, unknown> | null;
      if (snap?.verification) {
        const v = snap.verification as Record<string, number>;
        setTransformResult({
          front_error: v.front_error_m,
          rear_error: v.rear_error_m,
          system_id: result.system_id,
        });
      }
      // Prefetch landmarks GLB
      if (landmarksGlbUrl) URL.revokeObjectURL(landmarksGlbUrl);
      systemsApi.getLandmarksGlbUrl(result.system_id)
        .then(setLandmarksGlbUrl)
        .catch(() => {});
      notifications.show({ message: `Transform started: ${result.geometry_name}`, color: "teal" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

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
    return geometries.flatMap(
      (g) => (g.analysis_result as { parts?: string[] } | null)?.parts ?? []
    );
  }, [geometries]);

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

      <Divider label="Ride Height Transform" labelPosition="left" />

      <Select
        label="Condition Map"
        placeholder="Select map..."
        data={conditionMaps.map((m) => ({ value: m.id, label: m.name }))}
        value={selectedConditionMapId}
        onChange={(v) => { setSelectedConditionMapId(v); setSelectedConditionId(null); }}
        clearable
        size="sm"
      />
      <Select
        label="Condition"
        placeholder={selectedConditionMapId ? "Select condition..." : "Select map first"}
        data={conditions.map((c) => ({ value: c.id, label: c.name }))}
        value={selectedConditionId}
        onChange={setSelectedConditionId}
        disabled={!selectedConditionMapId}
        clearable
        size="sm"
      />
      {selectedCondition && (
        <Stack gap={4}>
          <Text size="xs" c="dimmed">
            {selectedCondition.inflow_velocity} m/s · yaw {selectedCondition.yaw_angle}°
            {selectedCondition.ride_height?.enabled && (
              <> · <Badge size="xs" color="teal">Ride Height</Badge></>
            )}
          </Text>
        </Stack>
      )}
      <Select
        label="Geometry to transform"
        placeholder="Select geometry..."
        data={geometries
          .filter((g) => g.status === "ready")
          .map((g) => ({ value: g.id, label: g.name }))}
        value={selectedGeometryId}
        onChange={setSelectedGeometryId}
        disabled={!selectedCondition?.ride_height?.enabled}
        clearable
        size="sm"
      />
      <Button
        size="sm"
        leftSection={<IconArrowDown size={14} />}
        disabled={!selectedCondition?.ride_height?.enabled || !selectedGeometryId}
        loading={transformMutation.isPending}
        onClick={() => transformMutation.mutate()}
        variant="light"
        color="teal"
      >
        Apply Ride Height Transform
      </Button>
      {transformResult && (
        <Stack gap={2}>
          <Text size="xs" fw={500}>Transform verification</Text>
          <Table fz="xs" withTableBorder>
            <Table.Tbody>
              <Table.Tr>
                <Table.Td>Front error</Table.Td>
                <Table.Td c={Math.abs(transformResult.front_error) < 0.001 ? "teal" : "orange"}>
                  {(transformResult.front_error * 1000).toFixed(2)} mm
                </Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Rear error</Table.Td>
                <Table.Td c={Math.abs(transformResult.rear_error) < 0.001 ? "teal" : "orange"}>
                  {(transformResult.rear_error * 1000).toFixed(2)} mm
                </Table.Td>
              </Table.Tr>
            </Table.Tbody>
          </Table>
        </Stack>
      )}

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
          <ControlPanel geometries={geometries} />
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
