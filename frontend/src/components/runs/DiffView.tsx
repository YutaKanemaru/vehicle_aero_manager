import { Modal, Table, Badge, Text, Loader, Stack } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { runsApi } from "../../api/configurations";
import type { RunResponse } from "../../api/configurations";

interface Props {
  opened: boolean;
  onClose: () => void;
  runAId: string;
  runBId: string;
  runs: RunResponse[];
}

export function DiffView({ opened, onClose, runAId, runBId, runs }: Props) {
  const { data: diff, isLoading } = useQuery({
    queryKey: ["diff", runAId, runBId],
    queryFn: () => runsApi.diff(runAId, runBId),
    enabled: opened,
  });

  const runA = runs.find((r) => r.id === runAId);
  const runB = runs.find((r) => r.id === runBId);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Settings Diff"
      size="xl"
    >
      <Stack gap="md">
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Field</Table.Th>
              <Table.Th>
                <Badge color="blue" variant="light">
                  {runA?.name ?? runAId}
                </Badge>
              </Table.Th>
              <Table.Th>
                <Badge color="green" variant="light">
                  {runB?.name ?? runBId}
                </Badge>
              </Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {isLoading ? (
              <Table.Tr>
                <Table.Td colSpan={3}>
                  <Loader size="sm" />
                </Table.Td>
              </Table.Tr>
            ) : diff?.changed_fields.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={3}>
                  <Text c="dimmed" ta="center">
                    No differences found
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              diff?.changed_fields.map((row) => (
                <Table.Tr key={row.field}>
                  <Table.Td>
                    <Text size="sm" ff="monospace">
                      {row.field}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="blue">
                      {row.run_a_value ?? "—"}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="green">
                      {row.run_b_value ?? "—"}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
      </Stack>
    </Modal>
  );
}
