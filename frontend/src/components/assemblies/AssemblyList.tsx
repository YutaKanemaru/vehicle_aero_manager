import {
  Table,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Badge,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconStack2,
  IconRefresh,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import { assembliesApi, type AssemblyResponse } from "../../api/geometries";
import { useAuthStore } from "../../stores/auth";
import { AssemblyCreateModal } from "./AssemblyCreateModal";
import { AssemblyGeometriesDrawer } from "./AssemblyGeometriesDrawer";

export function AssemblyList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [drawerAssembly, setDrawerAssembly] = useState<AssemblyResponse | null>(null);

  const { data: assemblies = [], isLoading, refetch } = useQuery({
    queryKey: ["assemblies"],
    queryFn: assembliesApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => assembliesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      notifications.show({ message: "Assembly deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  async function openDrawer(assembly: AssemblyResponse) {
    // fetch fresh detail (includes geometries[])
    const detail = await assembliesApi.get(assembly.id);
    setDrawerAssembly(detail);
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Assemblies</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconPlus size={16} />} onClick={openCreate}>
            New Assembly
          </Button>
        </Group>
      </Group>

      {assemblies.length === 0 && !isLoading ? (
        <Text c="dimmed" ta="center" py="xl">
          No assemblies yet. Create one and assign geometries to it.
        </Text>
      ) : (
        <Table highlightOnHover withTableBorder withColumnBorders>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Description</Table.Th>
              <Table.Th>Template</Table.Th>
              <Table.Th>Geometries</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {assemblies.map((a) => (
              <Table.Tr key={a.id}>
                <Table.Td>
                  <Text size="sm" fw={500}>{a.name}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed" lineClamp={1}>{a.description || "—"}</Text>
                </Table.Td>
                <Table.Td>
                  {a.template_id ? (
                    <Badge variant="outline" size="sm">Linked</Badge>
                  ) : (
                    <Text size="sm" c="dimmed">—</Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{a.geometries?.length ?? 0}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="xs">{new Date(a.created_at).toLocaleDateString()}</Text>
                </Table.Td>
                <Table.Td>
                  <Group gap={4} justify="flex-end">
                    <Tooltip label="Manage geometries">
                      <ActionIcon
                        variant="subtle"
                        size="sm"
                        onClick={() => openDrawer(a)}
                      >
                        <IconStack2 size={14} />
                      </ActionIcon>
                    </Tooltip>
                    {user && (user.id === a.created_by || user.is_admin) && (
                      <Tooltip label="Delete">
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          loading={deleteMutation.isPending}
                          onClick={() => deleteMutation.mutate(a.id)}
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

      <AssemblyCreateModal opened={createOpened} onClose={closeCreate} />
      <AssemblyGeometriesDrawer
        assembly={drawerAssembly}
        opened={drawerAssembly !== null}
        onClose={() => setDrawerAssembly(null)}
      />
    </Stack>
  );
}
