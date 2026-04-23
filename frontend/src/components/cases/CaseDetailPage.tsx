/**
 * CaseDetailPage — dedicated page at /cases/:caseId
 * 4 tabs: Information | Runs | Compare | Viewer
 */
import {
  Stack,
  Group,
  Text,
  Title,
  Badge,
  Tabs,
  ActionIcon,
  Tooltip,
  Button,
  TextInput,
  Textarea,
  Select,
  Table,
  Loader,
  Anchor,
  Checkbox,
  Paper,
  Divider,
  LoadingOverlay,
  ScrollArea,
  SimpleGrid,
  ThemeIcon,
  Code,
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
} from "@tabler/icons-react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState, useEffect } from "react";
import { useForm } from "@mantine/form";

import {
  casesApi,
  runsApi,
  conditionsApi,
  mapsApi,
  type CaseResponse,
  type RunResponse,
  type DiffField,
} from "../../api/configurations";
import { templatesApi } from "../../api/templates";
import { assembliesApi } from "../../api/geometries";

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
// Information Tab
// ---------------------------------------------------------------------------

function InformationTab({ caseData }: { caseData: CaseResponse }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);

  const { data: templates = [] } = useQuery({ queryKey: ["templates"], queryFn: templatesApi.list });
  const { data: assemblies = [] } = useQuery({ queryKey: ["assemblies"], queryFn: assembliesApi.list });
  const { data: maps = [] } = useQuery({ queryKey: ["maps"], queryFn: mapsApi.list });

  const form = useForm({
    initialValues: {
      name: caseData.name,
      description: caseData.description ?? "",
      template_id: caseData.template_id,
      assembly_id: caseData.assembly_id,
      map_id: caseData.map_id ?? null as string | null,
    },
  });

  useEffect(() => {
    form.setValues({
      name: caseData.name,
      description: caseData.description ?? "",
      template_id: caseData.template_id,
      assembly_id: caseData.assembly_id,
      map_id: caseData.map_id ?? null,
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
        map_id: v.map_id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case", caseData.id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case updated", color: "green" });
      setEditing(false);
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  return (
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
      <Select
        label="Template"
        required
        disabled={!editing}
        data={templates.map((t) => ({ value: t.id, label: t.name }))}
        {...form.getInputProps("template_id")}
      />
      <Select
        label="Assembly"
        required
        disabled={!editing}
        data={assemblies.map((a) => ({ value: a.id, label: a.name }))}
        {...form.getInputProps("assembly_id")}
      />
      <Select
        label="Condition Map"
        clearable
        disabled={!editing}
        data={maps.map((m) => ({ value: m.id, label: m.name }))}
        {...form.getInputProps("map_id")}
      />

      {/* Parent case */}
      {caseData.parent_case_id && (
        <>
          <Divider label="Origin" labelPosition="left" />
          <Group gap="xs">
            <Text size="sm" c="dimmed" w={120}>Created from</Text>
            <Anchor component={Link} to={`/cases/${caseData.parent_case_id}`} size="sm">
              <Group gap={6}>
                <Badge variant="outline" color="orange" size="sm">
                  {caseData.parent_case_number || caseData.parent_case_id.slice(0, 8)}
                </Badge>
                <Text size="sm">{caseData.parent_case_name}</Text>
              </Group>
            </Anchor>
          </Group>
        </>
      )}
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Runs Tab
// ---------------------------------------------------------------------------

function RunsTab({ caseData }: { caseData: CaseResponse }) {
  const queryClient = useQueryClient();
  const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [geometryOnly, setGeometryOnly] = useState<Record<string, boolean>>({});

  const { data: conditions = [] } = useQuery({
    queryKey: ["conditions", caseData.map_id],
    queryFn: () => conditionsApi.list(caseData.map_id!),
    enabled: !!caseData.map_id,
  });

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["runs", caseData.id],
    queryFn: () => runsApi.list(caseData.id),
    refetchInterval: (query) => {
      const hasActive = (query.state.data ?? []).some(
        (r: RunResponse) => r.status === "generating"
      );
      return hasActive ? 3000 : false;
    },
  });

  const selectedCond = conditions.find((c) => c.id === selectedConditionId);
  const previewName = selectedCond
    ? `${caseData.case_number}_R${(runs.length + 1).toString().padStart(2, "0")}_${selectedCond.name}${comment ? `_${comment}` : ""}`
    : "";

  const createRun = useMutation({
    mutationFn: () =>
      runsApi.create(caseData.id, {
        condition_id: selectedConditionId!,
        comment,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Run created", color: "green" });
      setSelectedConditionId(null);
      setComment("");
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const generateMutation = useMutation({
    mutationFn: ({ runId, gOnly }: { runId: string; gOnly: boolean }) =>
      runsApi.generate(caseData.id, runId, gOnly),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseData.id] });
      notifications.show({ message: "XML generation started", color: "blue" });
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

  async function downloadXml(runId: string) {
    try {
      const blob = await runsApi.download(caseData.id, runId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "output.xml";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      notifications.show({ message: (e as Error).message, color: "red" });
    }
  }

  const conditionOptions = conditions.map((c) => ({
    value: c.id,
    label: `${c.name} — ${c.inflow_velocity} m/s, yaw ${c.yaw_angle}°`,
  }));

  const hasParent = !!caseData.parent_case_id;

  if (!caseData.map_id) {
    return (
      <Text c="dimmed" size="sm" pt="md">
        No Condition Map assigned. Go to Information tab to assign a map.
      </Text>
    );
  }

  return (
    <Stack gap="md" pt="md">
      {/* Create Run Form */}
      <Paper withBorder p="sm" radius="sm">
        <Text size="sm" fw={600} mb="xs">New Run</Text>
        <Group align="flex-end" wrap="wrap">
          <Select
            label="Condition"
            placeholder="Select condition"
            data={conditionOptions}
            value={selectedConditionId}
            onChange={setSelectedConditionId}
            w={280}
          />
          <TextInput
            label="Comment (optional)"
            placeholder="e.g. draft_v2"
            value={comment}
            onChange={(e) => setComment(e.currentTarget.value)}
            w={200}
          />
          <Button
            size="sm"
            disabled={!selectedConditionId}
            loading={createRun.isPending}
            onClick={() => createRun.mutate()}
          >
            + New Run
          </Button>
        </Group>
        {previewName && (
          <Text size="xs" c="dimmed" mt={6}>
            Auto name: <Code>{previewName}</Code>
          </Text>
        )}
      </Paper>

      {/* Run List */}
      {isLoading ? (
        <Loader size="sm" />
      ) : runs.length === 0 ? (
        <Text c="dimmed" size="sm">
          No runs yet. Select a condition and click &ldquo;+ New Run&rdquo;.
        </Text>
      ) : (
        <ScrollArea>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th style={{ width: 100 }}>#</Table.Th>
                <Table.Th>Name</Table.Th>
                <Table.Th>Condition</Table.Th>
                <Table.Th style={{ width: 100 }}>Status</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {runs.map((run) => {
                const condLabel = run.condition_name
                  ? `${run.condition_name} — ${run.condition_velocity} m/s, yaw ${run.condition_yaw}°`
                  : run.condition_id.slice(0, 8);
                return (
                  <Table.Tr key={run.id}>
                    <Table.Td>
                      <Badge variant="outline" color="gray" size="sm">
                        {run.run_number || "—"}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{run.name}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs" c="dimmed">{condLabel}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge color={STATUS_COLOR[run.status] ?? "gray"} size="sm">
                        {statusLabel(run.status)}
                      </Badge>
                      {run.status === "error" && run.error_message && (
                        <Tooltip label={run.error_message} multiline w={320}>
                          <ThemeIcon size="xs" color="red" variant="transparent" ml={4}>
                            <IconAlertCircle size={12} />
                          </ThemeIcon>
                        </Tooltip>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Group gap={4} wrap="nowrap">
                        {/* Geometry-only checkbox (only when parent exists and run is pending/error) */}
                        {hasParent && (run.status === "pending" || run.status === "error") && (
                          <Tooltip label="Only replace geometry (reuse parent XML settings)">
                            <Checkbox
                              size="xs"
                              label="Geom only"
                              checked={!!geometryOnly[run.id]}
                              onChange={(e) =>
                                setGeometryOnly((prev) => ({ ...prev, [run.id]: e.currentTarget.checked }))
                              }
                            />
                          </Tooltip>
                        )}
                        {/* Generate */}
                        {(run.status === "pending" || run.status === "error") && (
                          <Tooltip label="Generate XML">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="blue"
                              loading={generateMutation.isPending && generateMutation.variables?.runId === run.id}
                              onClick={() => generateMutation.mutate({ runId: run.id, gOnly: !!geometryOnly[run.id] })}
                            >
                              <IconPlayerPlay size={14} />
                            </ActionIcon>
                          </Tooltip>
                        )}
                        {/* Download XML */}
                        {run.status === "ready" && run.xml_path && (
                          <Tooltip label="Download XML">
                            <ActionIcon size="sm" variant="light" color="teal" onClick={() => downloadXml(run.id)}>
                              <IconDownload size={14} />
                            </ActionIcon>
                          </Tooltip>
                        )}
                        {/* Download STL */}
                        {run.status === "ready" && run.stl_path && (
                          <Tooltip label="Download STL">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="cyan"
                              component="a"
                              href={`/api/v1/cases/${caseData.id}/runs/${run.id}/download-stl`}
                            >
                              <IconFileTypography size={14} />
                            </ActionIcon>
                          </Tooltip>
                        )}
                        {/* Reset */}
                        {(run.status === "ready" || run.status === "error") && (
                          <Tooltip label="Reset to pending">
                            <ActionIcon
                              size="sm"
                              variant="light"
                              color="orange"
                              loading={resetMutation.isPending && resetMutation.variables === run.id}
                              onClick={() => {
                                if (confirm(`Reset run "${run.name}"? XML/STL files will be deleted.`))
                                  resetMutation.mutate(run.id);
                              }}
                            >
                              <IconRefresh size={14} />
                            </ActionIcon>
                          </Tooltip>
                        )}
                        {/* Delete */}
                        <Tooltip label="Delete run">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="red"
                            loading={deleteMutation.isPending && deleteMutation.variables === run.id}
                            onClick={() => {
                              if (confirm(`Delete run "${run.name}"?`)) deleteMutation.mutate(run.id);
                            }}
                          >
                            <IconTrash size={14} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        </ScrollArea>
      )}
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Compare Tab
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

function CompareTab({ caseData }: { caseData: CaseResponse }) {
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
          {/* Template settings diff */}
          <DiffTable title="Template Settings" items={result.template_settings_diff} />

          {/* Map / conditions diff */}
          <DiffTable title="Map Conditions" items={result.map_diff} />

          {/* Assembly parts diff */}
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
                        <Badge key={p} variant="light" color="green" size="xs" style={{ display: "block" }}>
                          {p}
                        </Badge>
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
                        <Badge key={p} variant="light" color="red" size="xs" style={{ display: "block" }}>
                          {p}
                        </Badge>
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
                      <Badge key={p} variant="outline" color="gray" size="xs" style={{ display: "block" }}>
                        {p}
                      </Badge>
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
          <Tabs.Tab value="information">Information</Tabs.Tab>
          <Tabs.Tab value="runs">
            Runs
          </Tabs.Tab>
          <Tabs.Tab value="compare">Compare</Tabs.Tab>
          <Tabs.Tab value="viewer">Viewer</Tabs.Tab>
        </Tabs.List>

        <ScrollArea style={{ flex: 1 }}>
          <Tabs.Panel value="information" px="md">
            <InformationTab caseData={caseData} />
          </Tabs.Panel>

          <Tabs.Panel value="runs" px="md">
            <RunsTab caseData={caseData} />
          </Tabs.Panel>

          <Tabs.Panel value="compare" px="md">
            <CompareTab caseData={caseData} />
          </Tabs.Panel>

          <Tabs.Panel value="viewer" px="md" pt="md">
            <Group gap="xs">
              <ThemeIcon color="gray" variant="light" size="sm"><IconInfoCircle size={12} /></ThemeIcon>
              <Text c="dimmed" size="sm">3D Viewer — coming soon (will reuse Template Builder canvas).</Text>
            </Group>
          </Tabs.Panel>
        </ScrollArea>
      </Tabs>
    </Stack>
  );
}
