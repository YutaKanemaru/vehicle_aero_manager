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
  IconPencil,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import {
  mapsApi,
  conditionsApi,
  type ConditionMapResponse,
  type ConditionResponse,
} from "../../api/configurations";
import { useAuthStore } from "../../stores/auth";
import { MapCreateModal } from "./MapCreateModal";
import { ConditionFormModal } from "./ConditionFormModal";

// ── Condition form inside the drawer ─────────────────────────────────────────

function ConditionSection({ map }: { map: ConditionMapResponse }) {
  const queryClient = useQueryClient();
  const [addOpened, { open: openAdd, close: closeAdd }] = useDisclosure(false);
  const [editCond, setEditCond] = useState<ConditionResponse | null>(null);

  const { data: conditions = [] } = useQuery({
    queryKey: ["conditions", map.id],
    queryFn: () => conditionsApi.list(map.id),
  });

  const deleteMutation = useMutation({
    mutationFn: (condId: string) => conditionsApi.delete(map.id, condId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conditions", map.id] });
      queryClient.invalidateQueries({ queryKey: ["maps"] });
      notifications.show({ message: "Condition deleted", color: "green" });
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Stack gap="md">
      {conditions.length === 0 ? (
        <Text c="dimmed" size="sm">No conditions yet.</Text>
      ) : (
        <Table striped>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Velocity (m/s)</Table.Th>
              <Table.Th>Yaw (deg)</Table.Th>
              <Table.Th>Ride Height</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {conditions.map((c) => (
              <Table.Tr key={c.id}>
                <Table.Td>{c.name}</Table.Td>
                <Table.Td>{c.inflow_velocity}</Table.Td>
                <Table.Td>{c.yaw_angle}</Table.Td>
                <Table.Td>
                  {c.ride_height?.enabled ? (
                    <Badge color="teal" variant="light" size="sm">Enabled</Badge>
                  ) : (
                    <Text size="xs" c="dimmed">—</Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      size="sm"
                      color="blue"
                      variant="subtle"
                      onClick={() => setEditCond(c)}
                    >
                      <IconPencil size={12} />
                    </ActionIcon>
                    <ActionIcon
                      size="sm"
                      color="red"
                      variant="subtle"
                      loading={deleteMutation.isPending && deleteMutation.variables === c.id}
                      onClick={() => {
                        if (confirm(`Delete condition "${c.name}"?`))
                          deleteMutation.mutate(c.id);
                      }}
                    >
                      <IconTrash size={12} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}

      <Group>
        <Button
          size="sm"
          leftSection={<IconPlus size={14} />}
          onClick={openAdd}
        >
          Add Condition
        </Button>
      </Group>

      {/* Add modal */}
      <ConditionFormModal
        opened={addOpened}
        onClose={closeAdd}
        mapId={map.id}
      />

      {/* Edit modal */}
      {editCond && (
        <ConditionFormModal
          opened={!!editCond}
          onClose={() => setEditCond(null)}
          mapId={map.id}
          condition={editCond}
        />
      )}
    </Stack>
  );
}

// ── MapList ───────────────────────────────────────────────────────────────────

export function MapList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [selectedMap, setSelectedMap] = useState<ConditionMapResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data: maps = [], isLoading, refetch } = useQuery({
    queryKey: ["maps"],
    queryFn: mapsApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => mapsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maps"] });
      notifications.show({ message: "Map deleted", color: "green" });
      setDrawerOpen(false);
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(m: ConditionMapResponse) {
    setSelectedMap(m);
    setDrawerOpen(true);
  }

  const canDelete = (m: ConditionMapResponse) =>
    m.created_by === user?.id || user?.is_admin;

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Condition Maps</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate}>
            New Map
          </Button>
        </Group>
      </Group>

      {maps.length === 0 && !isLoading ? (
        <Text c="dimmed" size="sm">
          No condition maps yet. Create a map and add conditions (velocity + yaw) to it.
        </Text>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Description</Table.Th>
              <Table.Th>Conditions</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {maps.map((m) => (
              <Table.Tr key={m.id} style={{ cursor: "pointer" }} onClick={() => openDrawer(m)}>
                <Table.Td>
                  <Text fw={500}>{m.name}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">{m.description ?? ""}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color="indigo">
                    {m.condition_count}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="xs" c="dimmed">
                    {new Date(m.created_at).toLocaleDateString()}
                  </Text>
                </Table.Td>
                <Table.Td onClick={(e) => e.stopPropagation()}>
                  <Group gap="xs" wrap="nowrap">
                    <Tooltip label="Manage Conditions">
                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="blue"
                        onClick={() => openDrawer(m)}
                      >
                        <IconSettings size={14} />
                      </ActionIcon>
                    </Tooltip>
                    {canDelete(m) && (
                      <Tooltip label="Delete">
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          color="red"
                          loading={deleteMutation.isPending && deleteMutation.variables === m.id}
                          onClick={() => {
                            if (confirm(`Delete map "${m.name}"?`)) deleteMutation.mutate(m.id);
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

      <MapCreateModal opened={createOpened} onClose={closeCreate} />

      {selectedMap && (
        <Drawer
          opened={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={
            <Stack gap={2}>
              <Text fw={600}>{selectedMap.name}</Text>
              {selectedMap.description && (
                <Text size="xs" c="dimmed">{selectedMap.description}</Text>
              )}
            </Stack>
          }
          position="right"
          size="lg"
        >
          <ConditionSection map={selectedMap} />
        </Drawer>
      )}
    </Stack>
  );
}
