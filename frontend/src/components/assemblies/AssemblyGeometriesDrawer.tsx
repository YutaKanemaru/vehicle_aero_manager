import {
  Drawer,
  Text,
  Stack,
  Group,
  Badge,
  ActionIcon,
  Tooltip,
  Divider,
  Box,
  Checkbox,
  Button,
  ScrollArea,
  Alert,
} from "@mantine/core";
import { IconTrash, IconPlus, IconAlertCircle } from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { assembliesApi, geometriesApi, type AssemblyResponse, type GeometryResponse } from "../../api/geometries";

function statusColor(status: string) {
  if (status === "ready") return "green";
  if (status === "error") return "red";
  if (status === "analyzing") return "blue";
  return "yellow";
}

interface Props {
  assembly: AssemblyResponse | null;
  opened: boolean;
  onClose: () => void;
}

export function AssemblyGeometriesDrawer({ assembly, opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);

  const { data: allGeometries = [] } = useQuery({
    queryKey: ["geometries"],
    queryFn: geometriesApi.list,
    enabled: opened,
  });

  const assemblyGeometryIds = new Set((assembly?.geometries ?? []).map((g: { id: string }) => g.id));
  const availableToAdd = allGeometries.filter(
    (g: GeometryResponse) => !assemblyGeometryIds.has(g.id) && g.status === "ready"
  );

  const addMutation = useMutation({
    mutationFn: (geometryId: string) => assembliesApi.addGeometry(assembly!.id, geometryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      setSelected([]);
      notifications.show({ message: "Geometry added", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const removeMutation = useMutation({
    mutationFn: (geometryId: string) => assembliesApi.removeGeometry(assembly!.id, geometryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      notifications.show({ message: "Geometry removed", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  if (!assembly) return null;

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title={<Text fw={600}>Geometries — {assembly.name}</Text>}
      position="right"
      size="md"
    >
      <Stack>
        <Box>
          <Text size="sm" fw={500} mb="xs">
            Current geometries ({(assembly.geometries ?? []).length})
          </Text>
          {(assembly.geometries ?? []).length === 0 ? (
            <Text size="sm" c="dimmed">No geometries assigned yet.</Text>
          ) : (
            <Stack gap={4}>
              {(assembly.geometries as GeometryResponse[]).map((g) => (
                <Group key={g.id} justify="space-between" p="xs" style={{ border: "1px solid var(--mantine-color-default-border)", borderRadius: 6 }}>
                  <Box>
                    <Text size="sm">{g.name}</Text>
                    <Group gap={6}>
                      <Badge color={statusColor(g.status)} size="xs">{g.status}</Badge>
                      <Text size="xs" c="dimmed">{g.original_filename}</Text>
                    </Group>
                  </Box>
                  <Tooltip label="Remove">
                    <ActionIcon
                      color="red"
                      variant="subtle"
                      size="sm"
                      loading={removeMutation.isPending}
                      onClick={() => removeMutation.mutate(g.id)}
                    >
                      <IconTrash size={14} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              ))}
            </Stack>
          )}
        </Box>

        <Divider />

        <Box>
          <Text size="sm" fw={500} mb="xs">Add geometries (ready only)</Text>
          {availableToAdd.length === 0 ? (
            <Alert icon={<IconAlertCircle size={14} />} color="gray">
              No ready geometries available to add.
            </Alert>
          ) : (
            <>
              <ScrollArea h={240}>
                <Stack gap={4}>
                  {availableToAdd.map((g: GeometryResponse) => (
                    <Group key={g.id} p="xs" style={{ border: "1px solid var(--mantine-color-default-border)", borderRadius: 6 }}>
                      <Checkbox
                        checked={selected.includes(g.id)}
                        onChange={(e) =>
                          setSelected(e.target.checked
                            ? [...selected, g.id]
                            : selected.filter((id) => id !== g.id)
                          )
                        }
                      />
                      <Box style={{ flex: 1 }}>
                        <Text size="sm">{g.name}</Text>
                        <Text size="xs" c="dimmed">{g.original_filename}</Text>
                      </Box>
                    </Group>
                  ))}
                </Stack>
              </ScrollArea>
              <Group justify="flex-end" mt="sm">
                <Button
                  leftSection={<IconPlus size={14} />}
                  size="xs"
                  disabled={selected.length === 0}
                  loading={addMutation.isPending}
                  onClick={() => selected.forEach((id) => addMutation.mutate(id))}
                >
                  Add selected ({selected.length})
                </Button>
              </Group>
            </>
          )}
        </Box>
      </Stack>
    </Drawer>
  );
}
