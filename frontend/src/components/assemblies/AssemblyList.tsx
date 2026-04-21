import {
  Table,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Collapse,
  Paper,
  Badge,
  Select,
  Popover,
  Modal,
  TextInput,
  Textarea,
  ThemeIcon,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconStack2,
  IconRefresh,
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
  assembliesApi,
  assemblyFoldersApi,
  type AssemblyResponse,
  type AssemblyFolderResponse,
} from "../../api/geometries";
import { useAuthStore } from "../../stores/auth";
import { AssemblyCreateModal } from "./AssemblyCreateModal";
import { AssemblyGeometriesDrawer } from "./AssemblyGeometriesDrawer";
import { useSortedItems, type SortKey } from "../../hooks/useSortedItems";

// ─── SortTh ──────────────────────────────────────────────────────────────────

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

// ─── Folder section ───────────────────────────────────────────────────────────

interface FolderSectionProps {
  folder: AssemblyFolderResponse | null;
  assemblies: AssemblyResponse[];
  folders: AssemblyFolderResponse[];
  canDeleteFolder: boolean;
  onDeleteFolder?: () => void;
  onOpenDrawer: (a: AssemblyResponse) => void;
  canDelete: (a: AssemblyResponse) => boolean;
  onDelete: (a: AssemblyResponse) => void;
  onMoveFolder: (assemblyId: string, folderId: string | null) => void;
}

function FolderSection({
  folder,
  assemblies,
  folders,
  canDeleteFolder,
  onDeleteFolder,
  onOpenDrawer,
  canDelete,
  onDelete,
  onMoveFolder,
}: FolderSectionProps) {
  const [open, setOpen] = useState(true);
  const label = folder ? folder.name : "Uncategorized";
  const icon = open ? <IconFolderOpen size={16} /> : <IconFolder size={16} />;
  const { sorted, sort, toggle } = useSortedItems(
    assemblies as unknown as Record<string, unknown>[]
  ) as { sorted: AssemblyResponse[]; sort: { key: SortKey; dir: "asc" | "desc" }; toggle: (k: SortKey) => void };

  const otherFolders = folders.filter((f) => f.id !== folder?.id);
  const folderOptions = [
    { value: "__none__", label: "— Uncategorized" },
    ...otherFolders.map((f) => ({ value: f.id, label: f.name })),
  ];

  return (
    <Paper withBorder p={0} mb="xs">
      <Group
        px="sm"
        py="xs"
        style={{ cursor: "pointer", userSelect: "none" }}
        onClick={() => setOpen((o) => !o)}
        justify="space-between"
      >
        <Group gap="xs">
          <ThemeIcon variant="light" size="sm" color="blue">{icon}</ThemeIcon>
          <Text fw={600} size="sm">{label}</Text>
          <Badge size="xs" variant="light" color="gray">{assemblies.length}</Badge>
        </Group>
        <Group gap="xs" onClick={(e) => e.stopPropagation()}>
          {folder && canDeleteFolder && (
            <Tooltip label="Delete folder">
              <ActionIcon size="xs" variant="subtle" color="red" onClick={onDeleteFolder}>
                <IconTrash size={12} />
              </ActionIcon>
            </Tooltip>
          )}
          {open ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
        </Group>
      </Group>

      <Collapse in={open}>
        {assemblies.length === 0 ? (
          <Text size="xs" c="dimmed" px="sm" pb="xs">No assemblies in this folder.</Text>
        ) : (
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <SortTh label="Name" sortKey="name" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
                <Table.Th>Geometries</Table.Th>
                <SortTh label="Created" sortKey="created_at" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {sorted.map((a) => (
                <Table.Tr key={a.id}>
                  <Table.Td>
                    <Text size="sm" fw={500}>{a.name}</Text>
                    {a.description && (
                      <Text size="xs" c="dimmed" lineClamp={1}>{a.description}</Text>
                    )}
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{(a.geometries?.length ?? 0)}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {new Date(a.created_at).toLocaleDateString()}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Group gap={4} justify="flex-end" wrap="nowrap">
                      <Tooltip label="Manage geometries">
                        <ActionIcon variant="subtle" size="sm" onClick={() => onOpenDrawer(a)}>
                          <IconStack2 size={14} />
                        </ActionIcon>
                      </Tooltip>
                      <Popover withinPortal position="bottom-end">
                        <Popover.Target>
                          <Tooltip label="Move to folder">
                            <ActionIcon variant="subtle" size="sm" color="blue">
                              <IconArrowRight size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Popover.Target>
                        <Popover.Dropdown>
                          <Select
                            placeholder="Select folder"
                            data={folderOptions}
                            size="xs"
                            w={180}
                            onChange={(val) => {
                              if (val !== null)
                                onMoveFolder(a.id, val === "__none__" ? null : val);
                            }}
                          />
                        </Popover.Dropdown>
                      </Popover>
                      {canDelete(a) && (
                        <Tooltip label="Delete">
                          <ActionIcon
                            color="red"
                            variant="subtle"
                            size="sm"
                            onClick={() => onDelete(a)}
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
      </Collapse>
    </Paper>
  );
}

// ─── New Folder Modal ─────────────────────────────────────────────────────────

function NewFolderModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm({ initialValues: { name: "", description: "" } });

  const mutation = useMutation({
    mutationFn: (v: { name: string; description: string }) =>
      assemblyFoldersApi.create({ name: v.name, description: v.description || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblyFolders"] });
      notifications.show({ message: "Folder created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="New Assembly Folder" size="sm">
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack gap="sm">
          <TextInput label="Name" required {...form.getInputProps("name")} />
          <Textarea label="Description" rows={2} {...form.getInputProps("description")} />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Create</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function AssemblyList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [folderOpened, { open: openFolder, close: closeFolder }] = useDisclosure(false);
  const [drawerAssemblyId, setDrawerAssemblyId] = useState<string | null>(null);

  const { data: assemblies = [], isLoading, refetch } = useQuery({
    queryKey: ["assemblies"],
    queryFn: assembliesApi.list,
  });

  const { data: folders = [] } = useQuery({
    queryKey: ["assemblyFolders"],
    queryFn: assemblyFoldersApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => assembliesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      notifications.show({ message: "Assembly deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const deleteFolderMutation = useMutation({
    mutationFn: (id: string) => assemblyFoldersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblyFolders"] });
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      notifications.show({ message: "Folder deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const moveMutation = useMutation({
    mutationFn: ({ id, folderId }: { id: string; folderId: string | null }) =>
      assembliesApi.update(id, { folder_id: folderId } as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(a: AssemblyResponse) {
    setDrawerAssemblyId(a.id);
  }

  const canDelete = (a: AssemblyResponse) =>
    a.created_by === user?.id || (user?.is_admin ?? false);

  const canDeleteFolder = (f: AssemblyFolderResponse) =>
    f.created_by === user?.id || (user?.is_admin ?? false);

  // Group assemblies by folder_id
  const byFolder = new Map<string | null, AssemblyResponse[]>();
  byFolder.set(null, []);
  for (const f of folders) byFolder.set(f.id, []);
  for (const a of assemblies) {
    const key = a.folder_id ?? null;
    if (!byFolder.has(key)) byFolder.set(null, [...(byFolder.get(null) ?? [])]);
    byFolder.get(key)!.push(a);
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
          <Button leftSection={<IconFolderPlus size={14} />} variant="default" onClick={openFolder}>
            New Folder
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={openCreate}>
            New Assembly
          </Button>
        </Group>
      </Group>

      {folders.map((f) => (
        <FolderSection
          key={f.id}
          folder={f}
          assemblies={byFolder.get(f.id) ?? []}
          folders={folders}
          canDeleteFolder={canDeleteFolder(f)}
          onDeleteFolder={() => {
            if (confirm(`Delete folder "${f.name}"? Assemblies will become uncategorized.`))
              deleteFolderMutation.mutate(f.id);
          }}
          onOpenDrawer={openDrawer}
          canDelete={canDelete}
          onDelete={(a) => {
            if (confirm(`Delete assembly "${a.name}"?`)) deleteMutation.mutate(a.id);
          }}
          onMoveFolder={(assemblyId, folderId) =>
            moveMutation.mutate({ id: assemblyId, folderId })
          }
        />
      ))}

      <FolderSection
        key="__uncategorized__"
        folder={null}
        assemblies={byFolder.get(null) ?? []}
        folders={folders}
        canDeleteFolder={false}
        onOpenDrawer={openDrawer}
        canDelete={canDelete}
        onDelete={(a) => {
          if (confirm(`Delete assembly "${a.name}"?`)) deleteMutation.mutate(a.id);
        }}
        onMoveFolder={(assemblyId, folderId) =>
          moveMutation.mutate({ id: assemblyId, folderId })
        }
      />

      <AssemblyCreateModal opened={createOpened} onClose={closeCreate} />
      <NewFolderModal opened={folderOpened} onClose={closeFolder} />
      <AssemblyGeometriesDrawer
        assemblyId={drawerAssemblyId}
        opened={drawerAssemblyId !== null}
        onClose={() => setDrawerAssemblyId(null)}
      />
    </Stack>
  );
}
