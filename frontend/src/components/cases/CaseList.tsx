import {
  Table,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Badge,
  Drawer,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconRefresh,
  IconSettings,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import { casesApi } from "../../api/configurations";
import type { CaseResponse } from "../../api/configurations";
import { useAuthStore } from "../../stores/auth";
import { CaseCreateModal } from "./CaseCreateModal";
import { RunList } from "../runs/RunList";

export function CaseList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [selectedCase, setSelectedCase] = useState<CaseResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data: cases = [], isLoading, refetch } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => casesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case deleted", color: "green" });
      if (selectedCase) setDrawerOpen(false);
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(c: CaseResponse) {
    setSelectedCase(c);
    setDrawerOpen(true);
  }

  const canDelete = (c: CaseResponse) =>
    c.created_by === user?.id || user?.is_admin;

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Cases</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate}>
            New Case
          </Button>
        </Group>
      </Group>

      {cases.length === 0 && !isLoading ? (
        <Text c="dimmed" size="sm">
          No cases yet. Create a case by linking a Template and Assembly.
        </Text>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Template</Table.Th>
              <Table.Th>Assembly</Table.Th>
              <Table.Th>Map</Table.Th>
              <Table.Th>Runs</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {cases.map((c) => (
              <Table.Tr key={c.id} style={{ cursor: "pointer" }} onClick={() => openDrawer(c)}>
                <Table.Td>
                  <Text fw={500}>{c.name}</Text>
                  {c.description && (
                    <Text size="xs" c="dimmed">
                      {c.description}
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color="violet">
                    {c.template_id.slice(0, 8)}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color="teal">
                    {c.assembly_id.slice(0, 8)}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  {c.map_id ? (
                    <Badge variant="dot" color="cyan" size="sm">
                      {c.map_id.slice(0, 8)}
                    </Badge>
                  ) : (
                    <Text size="xs" c="dimmed">—</Text>
                  )}
                </Table.Td>
                <Table.Td>{c.run_count ?? 0}</Table.Td>
                <Table.Td>
                  <Text size="xs" c="dimmed">
                    {new Date(c.created_at).toLocaleDateString()}
                  </Text>
                </Table.Td>
                <Table.Td onClick={(e) => e.stopPropagation()}>
                  <Group gap="xs" wrap="nowrap">
                    <Tooltip label="Open">
                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="blue"
                        onClick={() => openDrawer(c)}
                      >
                        <IconSettings size={14} />
                      </ActionIcon>
                    </Tooltip>
                    {canDelete(c) && (
                      <Tooltip label="Delete">
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          color="red"
                          loading={deleteMutation.isPending && deleteMutation.variables === c.id}
                          onClick={() => {
                            if (confirm(`Delete case "${c.name}"?`)) deleteMutation.mutate(c.id);
                          }}
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}

      <CaseCreateModal opened={createOpened} onClose={closeCreate} />

      {selectedCase && (
        <Drawer
          opened={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={
            <Stack gap={2}>
              <Text fw={600}>{selectedCase.name}</Text>
              {selectedCase.description && (
                <Text size="xs" c="dimmed">
                  {selectedCase.description}
                </Text>
              )}
            </Stack>
          }
          position="right"
          size="xl"
        >
          <RunList caseId={selectedCase.id} />
        </Drawer>
      )}
    </Stack>
  );
}
