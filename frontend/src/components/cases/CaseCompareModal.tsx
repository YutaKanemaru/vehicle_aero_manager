import {
  Modal,
  Grid,
  Stack,
  Text,
  Badge,
  Table,
  ScrollArea,
  Group,
  Divider,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { casesApi, runsApi } from "../../api/configurations";
import type { CaseResponse, RunResponse } from "../../api/configurations";

interface Props {
  caseIds: [string, string];
  opened: boolean;
  onClose: () => void;
}

const STATUS_COLOR: Record<string, string> = {
  pending:    "gray",
  generating: "blue",
  ready:      "green",
  error:      "red",
};

function CaseColumn({ caseId }: { caseId: string }) {
  const { data: cases = [] } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });
  const caseData: CaseResponse | undefined = cases.find((c) => c.id === caseId);

  const { data: runs = [], isLoading } = useQuery<RunResponse[]>({
    queryKey: ["runs", caseId],
    queryFn: () => runsApi.list(caseId),
    enabled: !!caseId,
  });

  return (
    <Stack gap="xs">
      {caseData && (
        <Stack gap={4}>
          <Group gap="xs">
            {caseData.case_number && (
              <Badge variant="outline" color="gray" size="sm">{caseData.case_number}</Badge>
            )}
            <Text fw={600} size="sm">{caseData.name}</Text>
          </Group>
          <Group gap="xs">
            <Badge variant="light" color="violet" size="xs">
              {caseData.template_name || caseData.template_id.slice(0, 8)}
            </Badge>
            <Badge variant="light" color="teal" size="xs">
              {caseData.assembly_name || caseData.assembly_id.slice(0, 8)}
            </Badge>
          </Group>
        </Stack>
      )}
      <Divider />
      <ScrollArea h={400} type="auto">
        {isLoading ? (
          <Text size="xs" c="dimmed">Loading…</Text>
        ) : runs.length === 0 ? (
          <Text size="xs" c="dimmed">No runs</Text>
        ) : (
          <Table fz="xs" withRowBorders>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>#</Table.Th>
                <Table.Th>Condition</Table.Th>
                <Table.Th>Vel</Table.Th>
                <Table.Th>Yaw</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {runs.map((r) => (
                <Table.Tr key={r.id}>
                  <Table.Td>
                    <Text size="xs" c="dimmed">{r.run_number || "—"}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" lineClamp={1}>{r.condition_name || "—"}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs">{r.condition_velocity ? `${r.condition_velocity} m/s` : "—"}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs">{r.condition_yaw !== undefined ? `${r.condition_yaw}°` : "—"}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge size="xs" color={STATUS_COLOR[r.status] ?? "gray"}>
                      {r.status}
                    </Badge>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </ScrollArea>
    </Stack>
  );
}

export function CaseCompareModal({ caseIds, opened, onClose }: Props) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Compare Cases"
      size="xl"
    >
      <Grid gutter="md">
        <Grid.Col span={6}>
          <CaseColumn caseId={caseIds[0]} />
        </Grid.Col>
        <Grid.Col span={6}>
          <CaseColumn caseId={caseIds[1]} />
        </Grid.Col>
      </Grid>
    </Modal>
  );
}
