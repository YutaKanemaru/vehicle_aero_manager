/**
 * MapChangeSyncModal — previews what happens when a Case's Condition Map changes.
 * Shows keep / add / orphan rows. Confirm applies the map change (PATCH).
 */
import {
  Modal,
  Stack,
  Group,
  Text,
  Badge,
  Table,
  Button,
  Loader,
  Divider,
  ThemeIcon,
  ScrollArea,
} from "@mantine/core";
import {
  IconCheck,
  IconPlus,
  IconAlertTriangle,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { casesApi, type SyncRunsPreviewItem } from "../../api/configurations";

interface MapChangeSyncModalProps {
  opened: boolean;
  onClose: () => void;
  caseId: string;
  newMapId: string;
  newMapName: string;
  onSuccess?: () => void;
}

function SyncTable({ items, color, icon }: { items: SyncRunsPreviewItem[]; color: string; icon: React.ReactNode }) {
  if (items.length === 0) return null;
  return (
    <Table fz="xs" striped>
      <Table.Thead>
        <Table.Tr>
          <Table.Th style={{ width: 30 }}>{icon}</Table.Th>
          <Table.Th>Condition</Table.Th>
          <Table.Th>Velocity</Table.Th>
          <Table.Th>Yaw</Table.Th>
          <Table.Th>Run Status</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {items.map((item, idx) => (
          <Table.Tr key={`${item.condition_id}-${idx}`}>
            <Table.Td>
              <Badge size="xs" color={color} variant="light">
                {item.action}
              </Badge>
            </Table.Td>
            <Table.Td>{item.condition_name}</Table.Td>
            <Table.Td>{item.inflow_velocity} m/s</Table.Td>
            <Table.Td>{item.yaw_angle}°</Table.Td>
            <Table.Td>
              {item.existing_run_status ? (
                <Badge size="xs" variant="dot">
                  {item.existing_run_status}
                </Badge>
              ) : (
                <Text size="xs" c="dimmed">new</Text>
              )}
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}

export function MapChangeSyncModal({
  opened,
  onClose,
  caseId,
  newMapId,
  newMapName,
  onSuccess,
}: MapChangeSyncModalProps) {
  const queryClient = useQueryClient();

  const { data: preview, isLoading, error } = useQuery({
    queryKey: ["caseSyncPreview", caseId, newMapId],
    queryFn: () => casesApi.syncPreview(caseId, newMapId),
    enabled: opened && !!newMapId,
  });

  const applyMutation = useMutation({
    mutationFn: () => casesApi.update(caseId, { map_id: newMapId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["runs", caseId] });
      notifications.show({ message: "Map changed and runs synced", color: "green" });
      onClose();
      onSuccess?.();
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  const orphanReady = (preview?.orphan ?? []).filter(
    (o: SyncRunsPreviewItem) => o.existing_run_status === "ready" || o.existing_run_status === "error"
  );
  const orphanPending = (preview?.orphan ?? []).filter(
    (o: SyncRunsPreviewItem) => o.existing_run_status === "pending"
  );

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`Switch to map: ${newMapName}`}
      size="lg"
    >
      <Stack gap="md">
        {isLoading && <Loader size="sm" />}
        {error && (
          <Text c="red" size="sm">{(error as Error).message}</Text>
        )}

        {preview && (
          <>
            <Text size="sm">
              Switching the Condition Map will synchronize runs automatically:
            </Text>

            {preview.keep.length > 0 && (
              <>
                <Group gap="xs">
                  <ThemeIcon size="xs" color="green" variant="light"><IconCheck size={10} /></ThemeIcon>
                  <Text size="sm" fw={600}>Keep ({preview.keep.length})</Text>
                  <Text size="xs" c="dimmed">— existing runs re-linked to matching conditions</Text>
                </Group>
                <ScrollArea.Autosize mah={200}>
                  <SyncTable
                    items={preview.keep}
                    color="green"
                    icon={<IconCheck size={10} />}
                  />
                </ScrollArea.Autosize>
              </>
            )}

            {preview.add.length > 0 && (
              <>
                <Group gap="xs">
                  <ThemeIcon size="xs" color="blue" variant="light"><IconPlus size={10} /></ThemeIcon>
                  <Text size="sm" fw={600}>Add ({preview.add.length})</Text>
                  <Text size="xs" c="dimmed">— new pending runs created</Text>
                </Group>
                <ScrollArea.Autosize mah={200}>
                  <SyncTable
                    items={preview.add}
                    color="blue"
                    icon={<IconPlus size={10} />}
                  />
                </ScrollArea.Autosize>
              </>
            )}

            {preview.orphan.length > 0 && (
              <>
                <Group gap="xs">
                  <ThemeIcon size="xs" color="orange" variant="light"><IconAlertTriangle size={10} /></ThemeIcon>
                  <Text size="sm" fw={600}>Orphan ({preview.orphan.length})</Text>
                  <Text size="xs" c="dimmed">— no matching condition in new map</Text>
                </Group>
                <ScrollArea.Autosize mah={200}>
                  <SyncTable
                    items={preview.orphan}
                    color="orange"
                    icon={<IconAlertTriangle size={10} />}
                  />
                </ScrollArea.Autosize>
                {orphanPending.length > 0 && (
                  <Text size="xs" c="orange">
                    {orphanPending.length} pending orphan run(s) will be deleted.
                  </Text>
                )}
                {orphanReady.length > 0 && (
                  <Text size="xs" c="dimmed">
                    {orphanReady.length} generated orphan run(s) will be preserved (not deleted).
                  </Text>
                )}
              </>
            )}

            <Divider />

            <Group justify="flex-end">
              <Button variant="subtle" onClick={onClose}>
                Cancel
              </Button>
              <Button
                color="blue"
                loading={applyMutation.isPending}
                onClick={() => applyMutation.mutate()}
              >
                Apply Map Change
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>
  );
}
