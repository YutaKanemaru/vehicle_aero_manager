/**
 * CaseDetailPage — dedicated page at /cases/:caseId
 *
 * 2 tabs:
 *   [Case Info & Compare]  — case metadata edit form + compare accordion
 *   [Runs]                 — run table; "Launch Viewer" button opens a fixed fullscreen overlay
 *
 * Template/Assembly are locked (disabled) when any run has status != "pending".
 * Map changes trigger MapChangeSyncModal for sync preview before applying.
 */
import {
  Stack,
  Group,
  Text,
  Title,
  Badge,
  Accordion,
  ActionIcon,
  Tooltip,
  Button,
  TextInput,
  Textarea,
  Select,
  Table,
  Tabs,
  Loader,
  Checkbox,
  Paper,
  Divider,
  LoadingOverlay,
  ScrollArea,
  SimpleGrid,
  ThemeIcon,
  Code,
  Menu,
} from "@mantine/core";
import {
  IconArrowLeft,
  IconPlayerPlay,
  IconDownload,
  IconRefresh,
  IconTrash,
  IconEdit,
  IconCheck,
  IconX,
  IconFileTypography,
  IconAlertCircle,
  IconInfoCircle,
  IconExternalLink,
  IconLock,
  IconTransform,
  IconRoad,
} from "@tabler/icons-react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState, useEffect, useMemo } from "react";
import { useForm } from "@mantine/form";

import {
  casesApi,
  runsApi,
  mapsApi,
  type CaseResponse,
  type RunResponse,
  type DiffField,
} from "../../api/configurations";
import { templatesApi } from "../../api/templates";
import { assembliesApi } from "../../api/geometries";
import { MapChangeSyncModal } from "./MapChangeSyncModal";
import { RunViewer } from "./RunViewer";
import { useJobsStore } from "../../stores/jobs";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_COLOR: Record<string, string> = {
  pending: "yellow",
  generating: "blue",
  ready: "green",
  error: "red",
};

function statusLabel(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ---------------------------------------------------------------------------
// Information Tab (with lock + map sync)
// ---------------------------------------------------------------------------

function InformationTab({ caseData, runs }: { caseData: CaseResponse; runs: RunResponse[] }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [mapSyncModalOpen, setMapSyncModalOpen] = useState(false);
  const [pendingMapId, setPendingMapId] = useState<string | null>(null);
  const [pendingMapName, setPendingMapName] = useState("");

  const { data: templates = [] } = useQuery({ queryKey: ["templates"], queryFn: templatesApi.list });
  const { data: assemblies = [] } = useQuery({ queryKey: ["assemblies"], queryFn: assembliesApi.list });
  const { data: maps = [] } = useQuery({ queryKey: ["maps"], queryFn: mapsApi.list });
  const { data: allCases = [] } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });

  // Lock: template/assembly locked when any run is non-pending
  const hasGenerated = useMemo(
    () => runs.some((r) => r.status !== "pending"),
    [runs],
  );

  const form = useForm({
    initialValues: {
      name: caseData.name,
      description: caseData.description ?? "",
      template_id: caseData.template_id,
      assembly_id: caseData.assembly_id,
      map_id: caseData.map_id ?? (null as string | null),
      parent_case_id: caseData.parent_case_id ?? (null as string | null),
    },
  });

  useEffect(() => {
    form.setValues({
      name: caseData.name,
      description: caseData.description ?? "",
      template_id: caseData.template_id,
      assembly_id: caseData.assembly_id,
      map_id: caseData.map_id ?? null,
      parent_case_id: caseData.parent_case_id ?? null,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseData.id]);

  const updateMutation = useMutation({
    mutationFn: (v: typeof form.values) =>
      casesApi.update(caseData.id, {
        name: v.name,
        description: v.description || undefined,
        template_id: v.template_id,
        assembly_id: v.assembly_id,
        // map_id handled separately via MapChangeSyncModal
        parent_case_id: v.parent_case_id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case", caseData.id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case updated", color: "green" });
      setEditing(false);
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function handleMapChange(newMapId: string | null) {
    if (newMapId === caseData.map_id) {
      form.setFieldValue("map_id", newMapId);
      return;
    }
    if (!newMapId) {
      // Clearing map — just update directly
      casesApi.update(caseData.id, { map_id: null }).then(() => {
        queryClient.invalidateQueries({ queryKey: ["case", caseData.id] });
        queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
        notifications.show({ message: "Map cleared", color: "green" });
        form.setFieldValue("map_id", null);
      });
      return;
    }
    // Has runs? Show sync preview
    if (runs.length > 0) {
      const mapObj = maps.find((m) => m.id === newMapId);
      setPendingMapId(newMapId);
      setPendingMapName(mapObj?.name ?? "");
      setMapSyncModalOpen(true);
    } else {
      // No runs — just set the map + auto-create runs
      casesApi.update(caseData.id, { map_id: newMapId }).then(() => {
        queryClient.invalidateQueries({ queryKey: ["case", caseData.id] });
        queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
        notifications.show({ message: "Map set", color: "green" });
        form.setFieldValue("map_id", newMapId);
      });
    }
  }

  return (
    <>
      <Stack gap="md" maw={640} pt="md">
        <Group justify="space-between">
          <Text fw={600} size="lg">Case Information</Text>
          {editing ? (
            <Group gap="xs">
              <Button
                size="xs"
                leftSection={<IconCheck size={12} />}
                loading={updateMutation.isPending}
                onClick={() => updateMutation.mutate(form.values)}
              >Save</Button>
              <Button size="xs" variant="subtle" leftSection={<IconX size={12} />} onClick={() => { form.reset(); setEditing(false); }}>
                Cancel
              </Button>
            </Group>
          ) : (
            <ActionIcon variant="subtle" onClick={() => setEditing(true)}>
              <IconEdit size={16} />
            </ActionIcon>
          )}
        </Group>

        {/* Case number (read-only) */}
        <Group gap="xs">
          <Text size="sm" c="dimmed" w={120}>Case Number</Text>
          <Badge variant="outline" color="gray">{caseData.case_number || "—"}</Badge>
        </Group>

        {/* Editable fields */}
        <TextInput
          label="Name"
          required
          disabled={!editing}
          {...form.getInputProps("name")}
        />
        <Textarea
          label="Description"
          autosize
          minRows={2}
          disabled={!editing}
          {...form.getInputProps("description")}
        />

        {/* Template — locked when generated runs exist */}
        <Select
          label={
            <Group gap={4}>
              <Text size="sm">Template</Text>
              {hasGenerated && editing && (
                <Tooltip label="Locked — runs with generated data exist. Reset or delete them to change.">
                  <ThemeIcon size="xs" color="orange" variant="transparent">
                    <IconLock size={12} />
                  </ThemeIcon>
                </Tooltip>
              )}
            </Group>
          }
          required
          disabled={!editing || hasGenerated}
          data={templates.map((t) => ({ value: t.id, label: t.name }))}
          {...form.getInputProps("template_id")}
        />

        {/* Assembly — locked when generated runs exist */}
        <Select
          label={
            <Group gap={4}>
              <Text size="sm">Assembly</Text>
              {hasGenerated && editing && (
                <Tooltip label="Locked — runs with generated data exist. Reset or delete them to change.">
                  <ThemeIcon size="xs" color="orange" variant="transparent">
                    <IconLock size={12} />
                  </ThemeIcon>
                </Tooltip>
              )}
            </Group>
          }
          required
          disabled={!editing || hasGenerated}
          data={assemblies.map((a) => ({ value: a.id, label: a.name }))}
          {...form.getInputProps("assembly_id")}
        />

        {/* Condition Map — locked when generated runs exist */}
        <Select
          label={
            <Group gap={4}>
              <Text size="sm">Condition Map</Text>
              {hasGenerated && editing && (
                <Tooltip label="Locked — runs with generated data exist. Reset or delete them to change.">
                  <ThemeIcon size="xs" color="orange" variant="transparent">
                    <IconLock size={12} />
                  </ThemeIcon>
                </Tooltip>
              )}
            </Group>
          }
          clearable
          disabled={!editing || hasGenerated}
          data={maps.map((m) => ({ value: m.id, label: m.name }))}
          value={form.values.map_id}
          onChange={handleMapChange}
        />

        <Select
          label="Parent Case"
          description="Branch origin — set automatically when using Create Child Case"
          clearable
          disabled={!editing}
          data={allCases
            .filter((c) => c.id !== caseData.id)
            .map((c) => ({ value: c.id, label: `${c.case_number ? c.case_number + " — " : ""}${c.name}` }))}
          {...form.getInputProps("parent_case_id")}
        />
      </Stack>

      {/* Map Change Sync Modal */}
      {pendingMapId && (
        <MapChangeSyncModal
          opened={mapSyncModalOpen}
          onClose={() => {
            setMapSyncModalOpen(false);
            setPendingMapId(null);
          }}
          caseId={caseData.id}
          newMapId={pendingMapId}
          newMapName={pendingMapName}
          onSuccess={() => {
            form.setFieldValue("map_id", pendingMapId);
            setPendingMapId(null);
          }}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Runs & Viewer Tab
// ---------------------------------------------------------------------------

function RunsViewerTab({ caseData }: { caseData: CaseResponse }) {
  const queryClient = useQueryClient();
  const [geometryOnly, setGeometryOnly] = useState<Record<string, boolean>>({});
  const [viewerRun, setViewerRun] = useState<RunResponse | null>(null);

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["runs", caseData.id],
    queryFn: () => runsApi.list(caseData.id),
    refetchInterval: (query) => {
      const data = query.state.data ?? [];
      const hasActive = data.some(
        (r: RunResponse) => r.status === "generating"
      );
      // Also poll when transforms were just applied (geometry may still be processing)
      const hasTransformPending = data.some(
        (r: RunResponse) => r.needs_transform && r.transform_applied && (r.status === "pending" || r.status === "error")
      );
      return (hasActive || hasTransformPending) ? 3000 : false;
    },
  });

  const generateMutation = useMutation({
    mutationFn: ({ runId, gOnly }: { runId: string; gOnly: boolean }) =>
      runsApi.generate(caseData.id, runId, gOnly),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      notifications.show({ message: "XML generation started", color: "blue" });
      addJob(result.id, result.name, "xml_generation", { caseId: caseData.id });
      updateJob(result.id, "generating");
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const generateAllMutation = useMutation({
    mutationFn: async () => {
      const generatableRuns = runs.filter(
        (r) => (r.status === "pending" || r.status === "error") && (!r.needs_transform || r.transform_applied)
      );
      const results = await Promise.allSettled(
        generatableRuns.map((run) => runsApi.generate(caseData.id, run.id, false))
      );
      return { results, runs: generatableRuns };
    },
    onSuccess: ({ results, runs: generatedRuns }) => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      let successCount = 0;
      results.forEach((r, i) => {
        if (r.status === "fulfilled") {
          successCount++;
          const result = r.value;
          addJob(result.id, result.name, "xml_generation", { caseId: caseData.id });
          updateJob(result.id, "generating");
        } else {
          const run = generatedRuns[i];
          notifications.show({
            message: `XML generation failed for run "${run.name}": ${r.reason?.message ?? r.reason}`,
            color: "red",
          });
        }
      });
      if (successCount > 0) {
        notifications.show({ message: `XML generation started for ${successCount} run(s)`, color: "blue" });
      }
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const resetMutation = useMutation({
    mutationFn: (runId: string) => runsApi.reset(caseData.id, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      notifications.show({ message: "Run reset to pending", color: "orange" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (runId: string) => runsApi.delete(caseData.id, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Run deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);

  const transformMutation = useMutation({
    mutationFn: (runId: string) => runsApi.transform(caseData.id, runId),
    onSuccess: (result, runId) => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      if (result?.geometry_id) {
        const runName = runs.find((r) => r.id === runId)?.name ?? result.geometry_name;
        addJob(result.geometry_id, runName, "stl_transform");
        updateJob(result.geometry_id, "pending");
      }
      notifications.show({ message: "Transform started — geometry building in background", color: "teal" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const transformAllMutation = useMutation({
    mutationFn: async () => {
      const needTransform = runs.filter(
        (r) => r.needs_transform && !r.transform_applied && (r.status === "pending" || r.status === "error")
      );
      // Use allSettled so one failure doesn't abort the rest
      const results = await Promise.allSettled(
        needTransform.map((run) => runsApi.transform(caseData.id, run.id))
      );
      return { results, runs: needTransform };
    },
    onSuccess: ({ results, runs: transformedRuns }) => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      let successCount = 0;
      results.forEach((r, i) => {
        if (r.status === "fulfilled") {
          successCount++;
          const result = r.value;
          const run = transformedRuns[i];
          if (result?.geometry_id) {
            addJob(result.geometry_id, run.name, "stl_transform");
            updateJob(result.geometry_id, "pending");
          }
        } else {
          const run = transformedRuns[i];
          notifications.show({
            message: `Transform failed for run "${run.name}": ${r.reason?.message ?? r.reason}`,
            color: "red",
          });
        }
      });
      if (successCount > 0) {
        notifications.show({
          message: `${successCount} transform(s) started — geometries building in background`,
          color: "teal",
        });
      }
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const generateBeltsMutation = useMutation({
    mutationFn: (runId: string) => runsApi.generateBelts(caseData.id, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      notifications.show({ message: "Belt STL generated", color: "teal" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const generateAllBeltsMutation = useMutation({
    mutationFn: async () => {
      const needBelts = runs.filter((r) => r.needs_belt_generation);
      const results = await Promise.allSettled(
        needBelts.map((run) => runsApi.generateBelts(caseData.id, run.id))
      );
      return { results, runs: needBelts };
    },
    onSuccess: ({ results, runs: beltRuns }) => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      const successCount = results.filter((r) => r.status === "fulfilled").length;
      results.forEach((r, i) => {
        if (r.status === "rejected") {
          notifications.show({
            message: `Belt generation failed for "${beltRuns[i].name}": ${r.reason?.message ?? r.reason}`,
            color: "red",
          });
        }
      });
      if (successCount > 0) {
        notifications.show({ message: `${successCount} belt STL(s) generated`, color: "teal" });
      }
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  async function downloadXml(runId: string, runName: string) {
    try {
      const blob = await runsApi.download(caseData.id, runId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${runName}.xml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      notifications.show({ message: (e as Error).message, color: "red" });
    }
  }

  async function downloadStl(runId: string, runName: string) {
    try {
      const blob = await runsApi.downloadStl(caseData.id, runId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${runName}.stl`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      notifications.show({ message: (e as Error).message, color: "red" });
    }
  }

  async function downloadBeltStl(runId: string, runName: string) {
    try {
      const blob = await runsApi.downloadBeltStl(caseData.id, runId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${runName}_5belts.stl`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      notifications.show({ message: (e as Error).message, color: "red" });
    }
  }

  const hasParent = !!caseData.parent_case_id;
  const beltsNeededCount = runs.filter((r) => r.needs_belt_generation).length;
  const transformNeededCount = runs.filter(
    (r) => r.needs_transform && !r.transform_applied && (r.status === "pending" || r.status === "error")
  ).length;
  // Generate All: only runs that are ready to generate (pending/error + no transform needed OR transform already applied)
  const generatableCount = runs.filter(
    (r) => (r.status === "pending" || r.status === "error") && (!r.needs_transform || r.transform_applied)
  ).length;

  if (!caseData.map_id) {
    return (
      <Text c="dimmed" size="sm" p="md">
        No Condition Map assigned. Go to Case Info tab to assign a map.
      </Text>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "auto" }}>
      <Group px="sm" py={6} justify="space-between">
          <Text size="sm" fw={600}>Runs ({runs.length})</Text>
          <Group gap={4}>
            {beltsNeededCount > 0 && (
              <Button
                size="xs"
                variant="light"
                color="grape"
                leftSection={<IconRoad size={12} />}
                loading={generateAllBeltsMutation.isPending}
                onClick={() => generateAllBeltsMutation.mutate()}
              >
                Generate All Belts ({beltsNeededCount})
              </Button>
            )}
            {transformNeededCount > 0 && (
              <Button
                size="xs"
                variant="light"
                color="teal"
                leftSection={<IconTransform size={12} />}
                loading={transformAllMutation.isPending}
                onClick={() => transformAllMutation.mutate()}
              >
                Transform All ({transformNeededCount})
              </Button>
            )}
            {generatableCount > 0 && (
              <Button
                size="xs"
                variant="light"
                color="blue"
                leftSection={<IconPlayerPlay size={12} />}
                loading={generateAllMutation.isPending}
                onClick={() => generateAllMutation.mutate()}
              >
                Generate All ({generatableCount})
              </Button>
            )}
          </Group>
        </Group>

        {isLoading ? (
          <Loader size="sm" mx="md" />
        ) : runs.length === 0 ? (
          <Text c="dimmed" size="sm" mx="md" mb="sm">
            No runs. Assign a Condition Map to auto-create runs.
          </Text>
        ) : (
          <ScrollArea>
            <Table striped highlightOnHover fz="xs">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th style={{ width: 80 }}>#</Table.Th>
                  <Table.Th>Condition</Table.Th>
                  <Table.Th style={{ width: 90 }}>Velocity</Table.Th>
                  <Table.Th style={{ width: 60 }}>Yaw</Table.Th>
                  <Table.Th style={{ width: 90 }}>Status</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {runs.map((run) => {
                  return (
                    <Table.Tr key={run.id}>
                      <Table.Td>
                        <Badge variant="outline" color="gray" size="xs">
                          {run.run_number || "—"}
                        </Badge>
                      </Table.Td>
                      <Table.Td>{run.condition_name || run.condition_id.slice(0, 8)}</Table.Td>
                      <Table.Td>{run.condition_velocity} m/s</Table.Td>
                      <Table.Td>{run.condition_yaw}°</Table.Td>
                      <Table.Td>
                        <Group gap={2} wrap="nowrap">
                          <Badge color={STATUS_COLOR[run.status] ?? "gray"} size="xs">
                            {statusLabel(run.status)}
                          </Badge>
                          {run.status === "error" && run.error_message && (
                            <Tooltip label={run.error_message} multiline w={320}>
                              <ThemeIcon size="xs" color="red" variant="transparent">
                                <IconAlertCircle size={10} />
                              </ThemeIcon>
                            </Tooltip>
                          )}
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Group gap={2} wrap="nowrap" onClick={(e) => e.stopPropagation()}>
                          {/* Geometry-only checkbox */}
                          {hasParent && (run.status === "pending" || run.status === "error") && (
                            <Tooltip label="Only replace geometry (reuse parent XML settings)">
                              <Checkbox
                                size="xs"
                                label="Geom"
                                checked={!!geometryOnly[run.id]}
                                onChange={(e) => {
                                  const checked = e.currentTarget.checked;
                                  setGeometryOnly((prev) => ({ ...prev, [run.id]: checked }));
                                }}
                              />
                            </Tooltip>
                          )}
                          {/* Generate Belts */}
                          {run.needs_belt_generation && (
                            <Tooltip label="Generate Belt STL">
                              <ActionIcon
                                size="xs"
                                variant="light"
                                color="grape"
                                loading={generateBeltsMutation.isPending && generateBeltsMutation.variables === run.id}
                                onClick={() => generateBeltsMutation.mutate(run.id)}
                              >
                                <IconRoad size={12} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                          {/* Belt generated badge */}
                          {!!run.belt_stl_path && (
                            <Tooltip label="Belt STL generated">
                              <Badge size="xs" color="grape" variant="dot">B</Badge>
                            </Tooltip>
                          )}
                          {/* Apply Transform */}
                          {run.needs_transform && !run.transform_applied && (run.status === "pending" || run.status === "error") && (
                            <Tooltip label="Apply Transform (ride height / yaw)">
                              <ActionIcon
                                size="xs"
                                variant="light"
                                color="teal"
                                loading={transformMutation.isPending && transformMutation.variables === run.id}
                                onClick={() => transformMutation.mutate(run.id)}
                              >
                                <IconTransform size={12} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                          {/* Transform applied badge */}
                          {run.needs_transform && run.transform_applied && (
                            <Tooltip label="Transform applied">
                              <Badge size="xs" color="teal" variant="dot">T</Badge>
                            </Tooltip>
                          )}
                          {/* Generate — disabled when transform required but not applied/ready */}
                          {(run.status === "pending" || run.status === "error") && (() => {
                            const transformPending = run.needs_transform && !run.transform_applied;
                            const transformProcessing = run.needs_transform && run.transform_applied && run.geometry_override_status !== "ready";
                            const generateDisabled = transformPending || transformProcessing;
                            const generateLabel = transformPending
                              ? "Apply Transform first"
                              : transformProcessing
                              ? `Transform geometry processing (${run.geometry_override_status})…`
                              : "Generate XML";
                            return (
                              <Tooltip label={generateLabel}>
                                <ActionIcon
                                  size="xs"
                                  variant="light"
                                  color="blue"
                                  disabled={generateDisabled}
                                  loading={generateMutation.isPending && generateMutation.variables?.runId === run.id}
                                  onClick={() => generateMutation.mutate({ runId: run.id, gOnly: !!geometryOnly[run.id] })}
                                >
                                  <IconPlayerPlay size={12} />
                                </ActionIcon>
                              </Tooltip>
                            );
                          })()}
                          {/* Download XML */}
                          {run.status === "ready" && run.xml_path && (
                            <Tooltip label="Download XML">
                              <ActionIcon size="xs" variant="light" color="teal" onClick={() => downloadXml(run.id, run.name)}>
                                <IconDownload size={12} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                          {/* Download STL (dropdown when belt STL also available) */}
                          {run.status === "ready" && run.stl_path && (
                            run.belt_stl_path ? (
                              <Menu shadow="md" position="bottom-end">
                                <Menu.Target>
                                  <Tooltip label="Download STL">
                                    <ActionIcon size="xs" variant="light" color="cyan">
                                      <IconFileTypography size={12} />
                                    </ActionIcon>
                                  </Tooltip>
                                </Menu.Target>
                                <Menu.Dropdown>
                                  <Menu.Item
                                    leftSection={<IconFileTypography size={12} />}
                                    onClick={() => downloadStl(run.id, run.name)}
                                  >
                                    Download STL
                                  </Menu.Item>
                                  <Menu.Item
                                    leftSection={<IconRoad size={12} />}
                                    onClick={() => downloadBeltStl(run.id, run.name)}
                                  >
                                    Download Belt STL
                                  </Menu.Item>
                                </Menu.Dropdown>
                              </Menu>
                            ) : (
                              <Tooltip label="Download STL">
                                <ActionIcon
                                  size="xs"
                                  variant="light"
                                  color="cyan"
                                  onClick={() => downloadStl(run.id, run.name)}
                                >
                                  <IconFileTypography size={12} />
                                </ActionIcon>
                              </Tooltip>
                            )
                          )}
                          {/* Reset */}
                          {(run.status === "ready" || run.status === "error" || (run.status === "pending" && run.transform_applied)) && (() => {
                            const transformProcessing = run.transform_applied && run.geometry_override_status !== "ready" && run.geometry_override_status !== "error" && run.geometry_override_status !== null;
                            return (
                              <Tooltip label={transformProcessing ? "Cannot reset while transform geometry is processing" : "Reset to pending"}>
                                <ActionIcon
                                  size="xs"
                                  variant="light"
                                  color="orange"
                                  disabled={transformProcessing}
                                  loading={resetMutation.isPending && resetMutation.variables === run.id}
                                  onClick={() => {
                                    const msg = run.transform_applied
                                      ? `Reset run "${run.name}"? XML/STL files and the applied transform will be permanently deleted.`
                                      : `Reset run "${run.name}"? XML/STL files will be deleted.`;
                                    if (confirm(msg)) resetMutation.mutate(run.id);
                                  }}
                                >
                                  <IconRefresh size={12} />
                                </ActionIcon>
                              </Tooltip>
                            );
                          })()}
                          {/* Delete */}
                          {(() => {
                            const transformProcessing = run.transform_applied && run.geometry_override_status !== "ready" && run.geometry_override_status !== "error" && run.geometry_override_status !== null;
                            return (
                              <Tooltip label={transformProcessing ? "Cannot delete while transform geometry is processing" : "Delete run"}>
                                <ActionIcon
                                  size="xs"
                                  variant="light"
                                  color="red"
                                  disabled={transformProcessing}
                                  loading={deleteMutation.isPending && deleteMutation.variables === run.id}
                                  onClick={() => {
                                    if (confirm(`Delete run "${run.name}"?`)) deleteMutation.mutate(run.id);
                                  }}
                                >
                                  <IconTrash size={12} />
                                </ActionIcon>
                              </Tooltip>
                            );
                          })()}
                          {/* Launch Viewer */}
                          {run.status === "ready" && (
                            <Tooltip label="Open 3D Viewer">
                              <ActionIcon
                                size="xs"
                                variant="filled"
                                color="violet"
                                onClick={() => setViewerRun(run)}
                              >
                                <IconExternalLink size={12} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        )}

      {/* Fullscreen Run Viewer Overlay */}
      {viewerRun && (
        <div style={{
          position: "fixed",
          inset: 0,
          zIndex: 300,
          background: "var(--mantine-color-body)",
          display: "flex",
          flexDirection: "column",
        }}>
          <Group
            px="md"
            py="xs"
            style={{ borderBottom: "1px solid var(--mantine-color-default-border)", flexShrink: 0 }}
          >
            <Badge variant="outline" color="gray" size="sm">{viewerRun.run_number || "Run"}</Badge>
            <Text size="sm" fw={600} style={{ flex: 1 }}>
              {caseData.name} — {viewerRun.condition_name}
              {viewerRun.condition_velocity ? ` • ${viewerRun.condition_velocity} m/s` : ""}
              {viewerRun.condition_yaw ? `, yaw ${viewerRun.condition_yaw}°` : ""}
            </Text>
            <Tooltip label="Close viewer">
              <ActionIcon variant="subtle" color="gray" onClick={() => setViewerRun(null)}>
                <IconX size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
          <div style={{ flex: 1, minHeight: 0 }}>
            <RunViewer
              caseId={caseData.id}
              assemblyId={caseData.assembly_id}
              run={viewerRun}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Compare Section (inside accordion)
// ---------------------------------------------------------------------------

function DiffTable({ title, items }: { title: string; items: DiffField[] }) {
  if (items.length === 0) return (
    <Group gap="xs">
      <ThemeIcon size="sm" color="green" variant="light"><IconCheck size={12} /></ThemeIcon>
      <Text size="sm" c="dimmed">{title}: no differences</Text>
    </Group>
  );

  return (
    <Stack gap="xs">
      <Text fw={600} size="sm">{title} — {items.length} difference{items.length !== 1 ? "s" : ""}</Text>
      <ScrollArea h={280}>
        <Table striped fz="xs">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Field</Table.Th>
              <Table.Th>Base</Table.Th>
              <Table.Th>Compare</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((d) => (
              <Table.Tr key={d.field} style={{ background: "rgba(255,200,0,0.06)" }}>
                <Table.Td><Code fz="xs">{d.field}</Code></Table.Td>
                <Table.Td><Text c="red" fz="xs" style={{ wordBreak: "break-all" }}>{d.run_a_value ?? "—"}</Text></Table.Td>
                <Table.Td><Text c="green" fz="xs" style={{ wordBreak: "break-all" }}>{d.run_b_value ?? "—"}</Text></Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Stack>
  );
}

function CompareSection({ caseData }: { caseData: CaseResponse }) {
  const [withCaseId, setWithCaseId] = useState<string | null>(
    caseData.parent_case_id ?? null
  );

  const { data: allCases = [] } = useQuery({ queryKey: ["cases"], queryFn: casesApi.list });

  const { data: result, isLoading, error } = useQuery({
    queryKey: ["caseCompare", caseData.id, withCaseId],
    queryFn: () => casesApi.compare(caseData.id, withCaseId!),
    enabled: !!withCaseId && withCaseId !== caseData.id,
  });

  const caseOptions = allCases
    .filter((c) => c.id !== caseData.id)
    .map((c) => ({ value: c.id, label: `${c.case_number} — ${c.name}` }));

  return (
    <Stack gap="lg" pt="md">
      <Group align="flex-end">
        <Select
          label="Compare with"
          placeholder="Select a case"
          data={caseOptions}
          value={withCaseId}
          onChange={setWithCaseId}
          w={320}
          description={caseData.parent_case_id && withCaseId === caseData.parent_case_id ? "Auto-selected parent case" : undefined}
        />
        {withCaseId && (
          <Group gap="xs">
            <Badge variant="outline" color="gray">{caseData.case_number}</Badge>
            <Text size="sm" c="dimmed">vs</Text>
            <Badge variant="outline" color="orange">
              {allCases.find((c) => c.id === withCaseId)?.case_number || "?"}
            </Badge>
          </Group>
        )}
      </Group>

      {isLoading && <Loader size="sm" />}
      {error && (
        <Group gap="xs">
          <ThemeIcon color="red" size="sm"><IconAlertCircle size={12} /></ThemeIcon>
          <Text size="sm" c="red">{(error as Error).message}</Text>
        </Group>
      )}

      {result && (
        <Stack gap="xl">
          <DiffTable title="Template Settings" items={result.template_settings_diff} />
          <DiffTable title="Map Conditions" items={result.map_diff} />

          <Stack gap="xs">
            <Text fw={600} size="sm">Assembly Parts</Text>
            <SimpleGrid cols={3} spacing="xs">
              <Paper withBorder p="xs" radius="sm">
                <Text size="xs" fw={600} c="green" mb={6}>
                  Added ({result.parts_diff.added.length})
                </Text>
                {result.parts_diff.added.length === 0 ? (
                  <Text size="xs" c="dimmed">None</Text>
                ) : (
                  <ScrollArea h={160}>
                    <Stack gap={2}>
                      {result.parts_diff.added.map((p) => (
                        <Badge key={p} variant="light" color="green" size="xs" style={{ display: "block" }}>{p}</Badge>
                      ))}
                    </Stack>
                  </ScrollArea>
                )}
              </Paper>
              <Paper withBorder p="xs" radius="sm">
                <Text size="xs" fw={600} c="red" mb={6}>
                  Removed ({result.parts_diff.removed.length})
                </Text>
                {result.parts_diff.removed.length === 0 ? (
                  <Text size="xs" c="dimmed">None</Text>
                ) : (
                  <ScrollArea h={160}>
                    <Stack gap={2}>
                      {result.parts_diff.removed.map((p) => (
                        <Badge key={p} variant="light" color="red" size="xs" style={{ display: "block" }}>{p}</Badge>
                      ))}
                    </Stack>
                  </ScrollArea>
                )}
              </Paper>
              <Paper withBorder p="xs" radius="sm">
                <Text size="xs" fw={600} c="dimmed" mb={6}>
                  Common ({result.parts_diff.common.length})
                </Text>
                <ScrollArea h={160}>
                  <Stack gap={2}>
                    {result.parts_diff.common.map((p) => (
                      <Badge key={p} variant="outline" color="gray" size="xs" style={{ display: "block" }}>{p}</Badge>
                    ))}
                  </Stack>
                </ScrollArea>
              </Paper>
            </SimpleGrid>
          </Stack>
        </Stack>
      )}

      {!withCaseId && (
        <Group gap="xs" mt="md">
          <ThemeIcon color="gray" variant="light" size="sm"><IconInfoCircle size={12} /></ThemeIcon>
          <Text size="sm" c="dimmed">Select a case above to compare template settings, conditions, and assembly parts.</Text>
        </Group>
      )}
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const { data: caseData, isLoading } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId!),
    enabled: !!caseId,
  });

  // Always fetch runs so we can pass to InformationTab for lock check
  const { data: runs = [] } = useQuery({
    queryKey: ["runs", caseId],
    queryFn: () => runsApi.list(caseId!),
    enabled: !!caseId,
  });

  if (isLoading) return <LoadingOverlay visible />;
  if (!caseData) return <Text p="md" c="dimmed">Case not found.</Text>;

  return (
    <Stack h="100%" gap={0}>
      {/* Header */}
      <Group px="md" py="sm" gap="sm" style={{ borderBottom: "1px solid var(--mantine-color-default-border)" }}>
        <Tooltip label="Back to Cases">
          <ActionIcon variant="subtle" onClick={() => navigate("/cases")}>
            <IconArrowLeft size={16} />
          </ActionIcon>
        </Tooltip>
        <Badge variant="outline" color="gray" size="lg">{caseData.case_number}</Badge>
        <Title order={4} style={{ flex: 1 }}>{caseData.name}</Title>
        {caseData.parent_case_id && (
          <Tooltip label={`Forked from ${caseData.parent_case_number} — ${caseData.parent_case_name}`}>
            <Badge variant="dot" color="orange" size="sm">
              From {caseData.parent_case_number || "parent"}
            </Badge>
          </Tooltip>
        )}
        <Badge variant="light" color="violet" size="sm">{caseData.template_name}</Badge>
        <Badge variant="light" color="teal" size="sm">{caseData.assembly_name}</Badge>
        {caseData.map_id && <Badge variant="dot" color="cyan" size="sm">{caseData.map_name}</Badge>}
      </Group>

      {/* Tabs */}
      <Tabs defaultValue="runs" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Tabs.List px="md">
          <Tabs.Tab value="info">Case Info &amp; Compare</Tabs.Tab>
          <Tabs.Tab value="runs">Runs</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="info" style={{ flex: 1, overflow: "auto" }}>
          <ScrollArea style={{ height: "100%" }}>
            <Stack gap={0} px="md" pb="xl">
              <InformationTab caseData={caseData} runs={runs} />

              <Divider my="lg" />

              <Accordion variant="separated">
                <Accordion.Item value="compare">
                  <Accordion.Control>
                    <Text fw={600} size="sm">Compare with Parent Case</Text>
                  </Accordion.Control>
                  <Accordion.Panel>
                    <CompareSection caseData={caseData} />
                  </Accordion.Panel>
                </Accordion.Item>
              </Accordion>
            </Stack>
          </ScrollArea>
        </Tabs.Panel>

        <Tabs.Panel value="runs" style={{ flex: 1, minHeight: 0 }}>
          <RunsViewerTab caseData={caseData} />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
