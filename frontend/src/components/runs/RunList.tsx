import {
  Stack,
  Table,
  Badge,
  Group,
  Button,
  Select,
  Text,
  TextInput,
  ActionIcon,
  Tooltip,
  Loader,
} from "@mantine/core";
import { IconDownload, IconPlaystationTriangle, IconGitCompare } from "@tabler/icons-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { runsApi, conditionsApi } from "../../api/configurations";
import type { RunResponse } from "../../api/configurations";
import { casesApi } from "../../api/configurations";
import { DiffView } from "./DiffView";

const STATUS_COLOR: Record<string, string> = {
  pending: "yellow",
  generating: "blue",
  ready: "green",
  error: "red",
};

interface Props {
  caseId: string;
}

export function RunList({ caseId }: Props) {
  const queryClient = useQueryClient();
  const [diffA, setDiffA] = useState<string | null>(null);
  const [diffB, setDiffB] = useState<string | null>(null);
  const [diffOpen, setDiffOpen] = useState(false);
  const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
  const [runName, setRunName] = useState("");

  const { data: caseData } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId),
  });

  const mapId = caseData?.map_id ?? null;

  const { data: conditions = [] } = useQuery({
    queryKey: ["conditions", mapId],
    queryFn: () => conditionsApi.list(mapId!),
    enabled: !!mapId,
  });

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["runs", caseId],
    queryFn: () => runsApi.list(caseId),
    refetchInterval: (query) => {
      const hasActive = (query.state.data ?? []).some(
        (r: RunResponse) => r.status === "generating"
      );
      return hasActive ? 3000 : false;
    },
  });

  const createRun = useMutation({
    mutationFn: () =>
      runsApi.create(caseId, {
        name: runName.trim() || `Run ${(runs?.length ?? 0) + 1}`,
        condition_id: selectedConditionId!,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseId] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Run created", color: "green" });
      setSelectedConditionId(null);
      setRunName("");
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const generateXml = useMutation({
    mutationFn: (runId: string) => runsApi.generate(caseId, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", caseId] });
      notifications.show({ message: "XML generation started", color: "blue" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function downloadXml(runId: string) {
    const url = runsApi.downloadUrl(caseId, runId);
    const a = document.createElement("a");
    a.href = url;
    a.download = "output.xml";
    a.click();
  }

  function openDiff() {
    if (diffA && diffB && diffA !== diffB) setDiffOpen(true);
  }

  const conditionOptions = conditions.map((c) => ({
    value: c.id,
    label: `${c.name} — ${c.inflow_velocity} m/s, yaw ${c.yaw_angle}°`,
  }));
  const runOptions = runs.map((r) => ({ value: r.id, label: r.name }));

  if (!mapId) {
    return (
      <Text c="dimmed" size="sm">
        No Condition Map assigned to this case. Edit the case to assign a map before creating runs.
      </Text>
    );
  }

  return (
    <Stack gap="md">
      {/* Create run row */}
      <Group align="flex-end">
        <Select
          label="Condition"
          placeholder="Select condition"
          data={conditionOptions}
          value={selectedConditionId}
          onChange={setSelectedConditionId}
          w={300}
        />
        <TextInput
          label="Run name (optional)"
          placeholder={`Run ${runs.length + 1}`}
          value={runName}
          onChange={(e) => setRunName(e.currentTarget.value)}
          w={180}
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

      {/* Diff selector */}
      {runs.length >= 2 && (
        <Group>
          <Text size="sm">Diff:</Text>
          <Select placeholder="Run A" data={runOptions} value={diffA} onChange={setDiffA} w={160} />
          <Select placeholder="Run B" data={runOptions} value={diffB} onChange={setDiffB} w={160} />
          <Button
            size="sm"
            variant="light"
            leftSection={<IconGitCompare size={14} />}
            onClick={openDiff}
            disabled={!diffA || !diffB || diffA === diffB}
          >
            Compare
          </Button>
        </Group>
      )}

      {isLoading ? (
        <Loader size="sm" />
      ) : runs.length === 0 ? (
        <Text c="dimmed" size="sm">
          No runs yet. Select a condition and click "+ New Run".
        </Text>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Condition</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {runs.map((run) => {
              const cond = conditions.find((c) => c.id === run.condition_id);
              const condLabel = cond
                ? `${cond.name} (${cond.inflow_velocity} m/s)`
                : run.condition_id;
              return (
                <Table.Tr key={run.id}>
                  <Table.Td>{run.name}</Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {condLabel}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLOR[run.status] ?? "gray"}>
                      {run.status === "generating" ? (
                        <Group gap={4}>
                          <Loader size={10} color="white" />
                          generating
                        </Group>
                      ) : (
                        run.status
                      )}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      {run.status !== "generating" && !run.xml_path && (
                        <Tooltip label="Generate XML">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="blue"
                            loading={generateXml.isPending && generateXml.variables === run.id}
                            onClick={() => generateXml.mutate(run.id)}
                          >
                            <IconPlaystationTriangle size={14} />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      {run.status === "ready" && (
                        <Tooltip label="Download XML">
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="green"
                            onClick={() => downloadXml(run.id)}
                          >
                            <IconDownload size={14} />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      {run.error_message && (
                        <Text size="xs" c="red" title={run.error_message}>
                          error
                        </Text>
                      )}
                    </Group>
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      )}

      {diffOpen && diffA && diffB && (
        <DiffView
          opened={diffOpen}
          onClose={() => setDiffOpen(false)}
          runAId={diffA}
          runBId={diffB}
          runs={runs}
        />
      )}
    </Stack>
  );
}
