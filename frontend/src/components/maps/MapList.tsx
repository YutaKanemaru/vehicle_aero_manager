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
  Paper,
  Collapse,
  Modal,
  TextInput,
  Textarea,
  ThemeIcon,
  Select,
  Popover,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconRefresh,
  IconSettings,
  IconPencil,
  IconFolderPlus,
  IconFolder,
  IconFolderOpen,
  IconChevronDown,
  IconChevronRight,
  IconArrowRight,
  IconArrowUp,
  IconArrowDown,
  IconArrowsSort,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import { useForm } from "@mantine/form";
import {
  mapsApi,
  mapFoldersApi,
  conditionsApi,
  type ConditionMapResponse,
  type ConditionResponse,
  type ConditionMapFolderResponse,
} from "../../api/configurations";
import { useAuthStore } from "../../stores/auth";
import { MapCreateModal } from "./MapCreateModal";
import { ConditionFormModal } from "./ConditionFormModal";
import { useSortedItems, type SortKey } from "../../hooks/useSortedItems";

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

// ── SortTh ───────────────────────────────────────────────────────────────────

interface SortThProps {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  dir: "asc" | "desc";
  onToggle: (k: SortKey) => void;
}
function SortTh({ label, sortKey, activeKey, dir, onToggle }: SortThProps) {
  const active = sortKey === activeKey;
  return (
    <Table.Th>
      <Group gap={4} wrap="nowrap" style={{ cursor: "pointer" }} onClick={() => onToggle(sortKey)}>
        {label}
        {active
          ? dir === "asc" ? <IconArrowUp size={12} /> : <IconArrowDown size={12} />
          : <IconArrowsSort size={12} opacity={0.3} />}
      </Group>
    </Table.Th>
  );
}

// ── MapTable (inside folder) ──────────────────────────────────────────────────

function MapTable({
  maps,
  onRowClick,
  onDelete,
  onMoveFolder,
  folders,
  canDeleteFn,
  deletingId,
}: {
  maps: ConditionMapResponse[];
  onRowClick: (m: ConditionMapResponse) => void;
  onDelete: (m: ConditionMapResponse) => void;
  onMoveFolder: (mapId: string, folderId: string | null) => void;
  folders: ConditionMapFolderResponse[];
  canDeleteFn: (m: ConditionMapResponse) => boolean;
  deletingId: string | undefined;
}) {
  const { sorted, sort, toggle } = useSortedItems(
    maps as unknown as Record<string, unknown>[]
  ) as { sorted: ConditionMapResponse[]; sort: { key: SortKey; dir: "asc" | "desc" }; toggle: (k: SortKey) => void };

  if (maps.length === 0) {
    return <Text size="xs" c="dimmed" px="sm" pb="xs">No maps in this folder.</Text>;
  }

  return (
    <Table striped highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <SortTh label="Name" sortKey="name" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th>Description</Table.Th>
          <Table.Th>Conditions</Table.Th>
          <SortTh label="Created" sortKey="created_at" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th />
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {sorted.map((m) => (
          <Table.Tr key={m.id} style={{ cursor: "pointer" }} onClick={() => onRowClick(m)}>
            <Table.Td><Text fw={500}>{m.name}</Text></Table.Td>
            <Table.Td><Text size="sm" c="dimmed">{m.description ?? ""}</Text></Table.Td>
            <Table.Td>
              <Badge variant="light" color="indigo">{m.condition_count}</Badge>
            </Table.Td>
            <Table.Td>
              <Text size="xs" c="dimmed">{new Date(m.created_at).toLocaleDateString()}</Text>
            </Table.Td>
            <Table.Td onClick={(e) => e.stopPropagation()}>
              <Group gap={4} wrap="nowrap">
                <Tooltip label="Manage Conditions">
                  <ActionIcon size="sm" variant="subtle" color="blue" onClick={() => onRowClick(m)}>
                    <IconSettings size={14} />
                  </ActionIcon>
                </Tooltip>
                <Popover withinPortal position="bottom-end">
                  <Popover.Target>
                    <Tooltip label="Move to folder">
                      <ActionIcon size="sm" variant="subtle" color="blue">
                        <IconArrowRight size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Popover.Target>
                  <Popover.Dropdown>
                    <Select
                      placeholder="Select folder"
                      size="xs"
                      clearable
                      data={folders.map((f) => ({ value: f.id, label: f.name }))}
                      value={m.folder_id ?? null}
                      onChange={(v) => onMoveFolder(m.id, v)}
                    />
                  </Popover.Dropdown>
                </Popover>
                {canDeleteFn(m) && (
                  <Tooltip label="Delete">
                    <ActionIcon
                      size="sm"
                      variant="subtle"
                      color="red"
                      loading={deletingId === m.id}
                      onClick={() => onDelete(m)}
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
  );
}

// ── FolderSection ─────────────────────────────────────────────────────────────

function FolderSection({
  folder,
  maps,
  onRowClick,
  onDelete,
  onMoveFolder,
  folders,
  canDeleteFn,
  deletingId,
  canDeleteFolder,
  onDeleteFolder,
}: {
  folder: ConditionMapFolderResponse | null;
  maps: ConditionMapResponse[];
  onRowClick: (m: ConditionMapResponse) => void;
  onDelete: (m: ConditionMapResponse) => void;
  onMoveFolder: (mapId: string, folderId: string | null) => void;
  folders: ConditionMapFolderResponse[];
  canDeleteFn: (m: ConditionMapResponse) => boolean;
  deletingId: string | undefined;
  canDeleteFolder: boolean;
  onDeleteFolder: (id: string) => void;
}) {
  const [opened, { toggle }] = useDisclosure(true);
  const isUncategorized = folder === null;
  const label = isUncategorized ? "Uncategorized" : folder.name;

  return (
    <Paper withBorder radius="sm" mb="xs">
      <Group
        px="sm"
        py={6}
        justify="space-between"
        style={{ cursor: "pointer", userSelect: "none" }}
        onClick={toggle}
      >
        <Group gap="xs">
          <ThemeIcon size="sm" variant="light" color={isUncategorized ? "gray" : "blue"}>
            {opened
              ? <IconFolderOpen size={14} />
              : <IconFolder size={14} />}
          </ThemeIcon>
          <Text size="sm" fw={500}>{label}</Text>
          <Badge size="xs" variant="outline" color="gray">{maps.length}</Badge>
        </Group>
        <Group gap="xs" onClick={(e) => e.stopPropagation()}>
          {folder && canDeleteFolder && (
            <Tooltip label="Delete folder">
              <ActionIcon
                size="xs"
                variant="subtle"
                color="red"
                onClick={() => onDeleteFolder(folder.id)}
              >
                <IconTrash size={12} />
              </ActionIcon>
            </Tooltip>
          )}
          {opened ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
        </Group>
      </Group>

      <Collapse in={opened}>
        <MapTable
          maps={maps}
          onRowClick={onRowClick}
          onDelete={onDelete}
          onMoveFolder={onMoveFolder}
          folders={folders}
          canDeleteFn={canDeleteFn}
          deletingId={deletingId}
        />
      </Collapse>
    </Paper>
  );
}

// ── NewFolderModal ────────────────────────────────────────────────────────────

function NewFolderModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm({ initialValues: { name: "", description: "" } });

  const createMutation = useMutation({
    mutationFn: (vals: { name: string; description: string }) =>
      mapFoldersApi.create(vals),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mapFolders"] });
      notifications.show({ message: "Folder created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="New Folder" size="sm">
      <form onSubmit={form.onSubmit((v) => createMutation.mutate(v))}>
        <Stack gap="sm">
          <TextInput label="Name" required {...form.getInputProps("name")} />
          <Textarea label="Description" autosize minRows={2} {...form.getInputProps("description")} />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={createMutation.isPending}>Create</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

// ── MapList ───────────────────────────────────────────────────────────────────

export function MapList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [newFolderOpened, { open: openNewFolder, close: closeNewFolder }] = useDisclosure(false);
  const [selectedMap, setSelectedMap] = useState<ConditionMapResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data: maps = [], isLoading, refetch } = useQuery({
    queryKey: ["maps"],
    queryFn: mapsApi.list,
  });

  const { data: folders = [] } = useQuery({
    queryKey: ["mapFolders"],
    queryFn: mapFoldersApi.list,
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

  const deleteFolderMutation = useMutation({
    mutationFn: (id: string) => mapFoldersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mapFolders"] });
      queryClient.invalidateQueries({ queryKey: ["maps"] });
      notifications.show({ message: "Folder deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const moveMutation = useMutation({
    mutationFn: ({ id, folderId }: { id: string; folderId: string | null }) =>
      mapsApi.updateFolder(id, folderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["maps"] }),
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(m: ConditionMapResponse) {
    setSelectedMap(m);
    setDrawerOpen(true);
  }

  function handleDelete(m: ConditionMapResponse) {
    if (confirm(`Delete map "${m.name}"?`)) deleteMutation.mutate(m.id);
  }

  function handleDeleteFolder(id: string) {
    if (confirm("Delete folder? Maps will become uncategorized."))
      deleteFolderMutation.mutate(id);
  }

  const canDelete = (m: ConditionMapResponse) =>
    m.created_by === user?.id || user?.is_admin;

  // Group maps by folder
  const byFolder = new Map<string | null, ConditionMapResponse[]>();
  byFolder.set(null, []);
  for (const f of folders) byFolder.set(f.id, []);
  for (const m of maps) {
    const key = m.folder_id ?? null;
    const list = byFolder.get(key);
    if (list) list.push(m);
    else byFolder.get(null)!.push(m);
  }

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
          <Tooltip label="New Folder">
            <ActionIcon variant="subtle" onClick={openNewFolder}>
              <IconFolderPlus size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate}>
            New Map
          </Button>
        </Group>
      </Group>

      {maps.length === 0 && folders.length === 0 && !isLoading ? (
        <Text c="dimmed" size="sm">
          No condition maps yet. Create a map and add conditions (velocity + yaw) to it.
        </Text>
      ) : (
        <>
          {folders.map((f) => (
            <FolderSection
              key={f.id}
              folder={f}
              maps={byFolder.get(f.id) ?? []}
              onRowClick={openDrawer}
              onDelete={handleDelete}
              onMoveFolder={(id, folderId) => moveMutation.mutate({ id, folderId })}
              folders={folders}
              canDeleteFn={canDelete}
              deletingId={deleteMutation.isPending ? deleteMutation.variables ?? undefined : undefined}
              canDeleteFolder={!!(user?.is_admin)}
              onDeleteFolder={handleDeleteFolder}
            />
          ))}
          <FolderSection
            key="__uncategorized__"
            folder={null}
            maps={byFolder.get(null) ?? []}
            onRowClick={openDrawer}
            onDelete={handleDelete}
            onMoveFolder={(id, folderId) => moveMutation.mutate({ id, folderId })}
            folders={folders}
            canDeleteFn={canDelete}
            deletingId={deleteMutation.isPending ? deleteMutation.variables ?? undefined : undefined}
            canDeleteFolder={false}
            onDeleteFolder={() => {}}
          />
        </>
      )}

      <MapCreateModal opened={createOpened} onClose={closeCreate} />
      <NewFolderModal opened={newFolderOpened} onClose={closeNewFolder} />

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
