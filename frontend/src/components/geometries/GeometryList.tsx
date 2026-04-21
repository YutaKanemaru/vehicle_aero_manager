import {
  Table,
  Badge,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Collapse,
  Box,
  SimpleGrid,
  ScrollArea,
  NumberFormatter,
  Paper,
  Select,
  Popover,
  Modal,
  TextInput,
  Textarea as MantineTextarea,
  Divider,
  ThemeIcon,
} from "@mantine/core";
import {
  IconUpload,
  IconTrash,
  IconChevronDown,
  IconChevronRight,
  IconRefresh,
  IconFolderPlus,
  IconFolder,
  IconFolderOpen,
  IconArrowRight,
  IconLink,
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
  geometriesApi,
  foldersApi,
  type GeometryResponse,
  type GeometryFolderResponse,
} from "../../api/geometries";
import { useAuthStore } from "../../stores/auth";
import { useJobsStore } from "../../stores/jobs";
import { GeometryUploadModal } from "./GeometryUploadModal";
import { GeometryLinkModal } from "./GeometryLinkModal";
import { useSortedItems, type SortKey } from "../../hooks/useSortedItems";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function statusColor(status: string) {
  if (status === "ready") return "green";
  if (status === "error") return "red";
  if (status === "analyzing") return "blue";
  if (status === "ready-decimating") return "violet";
  return "yellow";
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

// ─── AnalysisDetails ─────────────────────────────────────────────────────────

function AnalysisDetails({ geometry }: { geometry: GeometryResponse }) {
  const result = geometry.analysis_result;
  if (!result) return <Text size="sm" c="dimmed">No analysis data</Text>;

  const dims = result.vehicle_dimensions;
  const bbox = result.vehicle_bbox;
  const partNames = Object.keys(result.part_info);

  return (
    <Box p="sm" style={{ borderRadius: 6, backgroundColor: "var(--mantine-color-default-hover)" }}>
      <SimpleGrid cols={2} spacing="xs" mb="xs">
        <Box>
          <Text size="xs" c="dimmed">Vehicle bounding box</Text>
          {bbox && (
            <Text size="xs" ff="monospace">
              X [{bbox.x_min.toFixed(3)}, {bbox.x_max.toFixed(3)}]<br />
              Y [{bbox.y_min.toFixed(3)}, {bbox.y_max.toFixed(3)}]<br />
              Z [{bbox.z_min.toFixed(3)}, {bbox.z_max.toFixed(3)}]
            </Text>
          )}
        </Box>
        <Box>
          <Text size="xs" c="dimmed">Dimensions (L × W × H)</Text>
          {dims && (
            <Text size="xs">
              {dims.length.toFixed(3)} m x {dims.width.toFixed(3)} m x {dims.height.toFixed(3)} m
            </Text>
          )}
        </Box>
      </SimpleGrid>
      <Text size="xs" c="dimmed" mb={4}>Parts ({partNames.length})</Text>
      <ScrollArea h={140}>
        <Table fz="xs" withColumnBorders withRowBorders={false}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Faces</Table.Th>
              <Table.Th>Vertices</Table.Th>
              <Table.Th>Centroid (x, y, z)</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {partNames.map((name) => {
              const p = result.part_info[name];
              return (
                <Table.Tr key={name}>
                  <Table.Td>{name}</Table.Td>
                  <Table.Td><NumberFormatter value={p.face_count} thousandSeparator /></Table.Td>
                  <Table.Td><NumberFormatter value={p.vertex_count} thousandSeparator /></Table.Td>
                  <Table.Td ff="monospace">
                    ({p.centroid[0].toFixed(3)}, {p.centroid[1].toFixed(3)}, {p.centroid[2].toFixed(3)})
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Box>
  );
}

// ─── GeometryRow ─────────────────────────────────────────────────────────────

interface GeometryRowProps {
  geometry: GeometryResponse;
  canDelete: boolean;
  folders: GeometryFolderResponse[];
}

function GeometryRow({ geometry, canDelete, folders }: GeometryRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const queryClient = useQueryClient();
  const removeJob = useJobsStore((s) => s.removeJob);

  const deleteMutation = useMutation({
    mutationFn: () => geometriesApi.delete(geometry.id),
    onSuccess: () => {
      removeJob(geometry.id);
      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      notifications.show({ message: "Geometry deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const moveMutation = useMutation({
    mutationFn: (folderId: string | null) => geometriesApi.updateFolder(geometry.id, folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      setMoveOpen(false);
      notifications.show({ message: "Moved", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const partCount = geometry.analysis_result
    ? Object.keys(geometry.analysis_result.part_info).length
    : null;

  const folderSelectData = [
    { value: "", label: "— No folder —" },
    ...folders.map((f) => ({ value: f.id, label: f.name })),
  ];

  return (
    <>
      <Table.Tr style={{ cursor: "pointer" }} onClick={() => setExpanded((v) => !v)}>
        <Table.Td>
          <Group gap={4}>
            {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
            <Text size="sm">{geometry.name}</Text>
            {geometry.is_linked && (
              <Tooltip label="リンク登録（ファイルはコピーされていません）" withArrow>
                <Badge size="xs" color="cyan" variant="light" leftSection={<IconLink size={10} />}>
                  Linked
                </Badge>
              </Tooltip>
            )}
          </Group>
        </Table.Td>
        <Table.Td>
          <Text size="xs" c="dimmed">{geometry.original_filename}</Text>
        </Table.Td>
        <Table.Td>
          <Text size="sm">{formatBytes(geometry.file_size)}</Text>
        </Table.Td>
        <Table.Td>
          <Badge color={statusColor(geometry.status)} size="sm">
            {geometry.status}
          </Badge>
        </Table.Td>
        <Table.Td>
          <Text size="sm">{partCount !== null ? partCount : "—"}</Text>
        </Table.Td>
        <Table.Td>
          <Text size="xs">{new Date(geometry.created_at).toLocaleDateString()}</Text>
        </Table.Td>
        <Table.Td onClick={(e) => e.stopPropagation()}>
          <Group gap={4} justify="flex-end">
            <Popover opened={moveOpen} onChange={setMoveOpen} position="bottom-end">
              <Popover.Target>
                <Tooltip label="Move to folder">
                  <ActionIcon
                    variant="subtle"
                    size="sm"
                    onClick={() => setMoveOpen((v) => !v)}
                  >
                    <IconArrowRight size={14} />
                  </ActionIcon>
                </Tooltip>
              </Popover.Target>
              <Popover.Dropdown p="xs" style={{ width: 200 }}>
                <Text size="xs" c="dimmed" mb={6}>Move to folder</Text>
                <Select
                  size="xs"
                  data={folderSelectData}
                  value={geometry.folder_id ?? ""}
                  onChange={(val) => moveMutation.mutate(val || null)}
                  disabled={moveMutation.isPending}
                />
              </Popover.Dropdown>
            </Popover>

            {canDelete && (
              <Tooltip label="Delete">
                <ActionIcon
                  color="red"
                  variant="subtle"
                  size="sm"
                  loading={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate()}
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        </Table.Td>
      </Table.Tr>
      {expanded && (
        <Table.Tr>
          <Table.Td colSpan={7} p={0}>
            <Collapse in={expanded}>
              <Box p="sm">
                {geometry.status === "error" && (
                  <Text size="sm" c="red">{geometry.error_message || "Analysis failed"}</Text>
                )}
                {geometry.status === "ready" && <AnalysisDetails geometry={geometry} />}
                {(geometry.status === "pending" || geometry.status === "analyzing") && (
                  <Text size="sm" c="dimmed">Analysis in progress...</Text>
                )}
                {geometry.status === "ready-decimating" && (
                  <Text size="sm" c="violet">Building 3D viewer cache...</Text>
                )}
              </Box>
            </Collapse>
          </Table.Td>
        </Table.Tr>
      )}
    </>
  );
}

// ─── GeometryTable ────────────────────────────────────────────────────────────

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

function GeometryTable({
  geometries,
  canDeleteFn,
  folders,
}: {
  geometries: GeometryResponse[];
  canDeleteFn: (g: GeometryResponse) => boolean;
  folders: GeometryFolderResponse[];
}) {
  const { sorted, sort, toggle } = useSortedItems(
    geometries as unknown as Record<string, unknown>[]
  ) as { sorted: GeometryResponse[]; sort: { key: SortKey; dir: "asc" | "desc" }; toggle: (k: SortKey) => void };

  if (geometries.length === 0) {
    return (
      <Text size="xs" c="dimmed" py="xs" ta="center">
        No geometries in this folder.
      </Text>
    );
  }
  return (
    <Table highlightOnHover withColumnBorders fz="sm">
      <Table.Thead>
        <Table.Tr>
          <SortTh label="Name" sortKey="name" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th>File</Table.Th>
          <Table.Th>Size</Table.Th>
          <Table.Th>Status</Table.Th>
          <Table.Th>Parts</Table.Th>
          <SortTh label="Uploaded" sortKey="created_at" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th />
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {sorted.map((g) => (
          <GeometryRow
            key={g.id}
            geometry={g}
            canDelete={canDeleteFn(g)}
            folders={folders}
          />
        ))}
      </Table.Tbody>
    </Table>
  );
}

// ─── FolderSection ────────────────────────────────────────────────────────────

interface FolderSectionProps {
  folder: GeometryFolderResponse | null;
  geometries: GeometryResponse[];
  canDeleteFn: (g: GeometryResponse) => boolean;
  folders: GeometryFolderResponse[];
  canDeleteFolder: boolean;
  onDeleteFolder: (id: string) => void;
}

function FolderSection({
  folder,
  geometries,
  canDeleteFn,
  folders,
  canDeleteFolder,
  onDeleteFolder,
}: FolderSectionProps) {
  const [opened, { toggle }] = useDisclosure(true);

  const isUncategorized = folder === null;
  const name = isUncategorized ? "Uncategorized" : folder.name;
  const color = isUncategorized ? "gray" : "yellow";

  return (
    <Paper withBorder p={0} style={{ overflow: "hidden" }}>
      <Group
        px="sm"
        py={8}
        justify="space-between"
        style={{
          cursor: "pointer",
          backgroundColor: "var(--mantine-color-default-hover)",
          borderBottom: opened ? "1px solid var(--mantine-color-default-border)" : "none",
        }}
        onClick={toggle}
      >
        <Group gap="xs">
          <ThemeIcon size={20} variant="light" color={color} radius="sm">
            {opened ? <IconFolderOpen size={12} /> : <IconFolder size={12} />}
          </ThemeIcon>
          <Text size="sm" fw={500}>{name}</Text>
          <Badge size="sm" color={color} variant="light">
            {geometries.length}
          </Badge>
        </Group>
        <Group gap="xs" onClick={(e) => e.stopPropagation()}>
          {!isUncategorized && canDeleteFolder && (
            <Tooltip label="Delete folder (geometries become uncategorized)">
              <ActionIcon
                size="sm"
                color="red"
                variant="subtle"
                onClick={() => onDeleteFolder(folder!.id)}
              >
                <IconTrash size={12} />
              </ActionIcon>
            </Tooltip>
          )}
          <ActionIcon size="sm" variant="subtle" onClick={toggle}>
            {opened ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}
          </ActionIcon>
        </Group>
      </Group>

      <Collapse in={opened}>
        <Box px="sm" py={4}>
          <GeometryTable
            geometries={geometries}
            canDeleteFn={canDeleteFn}
            folders={folders}
          />
        </Box>
      </Collapse>
    </Paper>
  );
}

// ─── FolderCreateModal ────────────────────────────────────────────────────────

interface FolderCreateModalProps {
  opened: boolean;
  onClose: () => void;
}

function FolderCreateModal({ opened, onClose }: FolderCreateModalProps) {
  const queryClient = useQueryClient();
  const form = useForm({
    initialValues: { name: "", description: "" },
    validate: { name: (v) => (v.trim() ? null : "Name is required") },
  });

  const mutation = useMutation({
    mutationFn: () =>
      foldersApi.create({
        name: form.values.name.trim(),
        description: form.values.description || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["geometry-folders"] });
      notifications.show({ message: "Folder created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="New Folder" size="sm">
      <form onSubmit={form.onSubmit(() => mutation.mutate())}>
        <Stack>
          <TextInput label="Folder name" required {...form.getInputProps("name")} />
          <MantineTextarea
            label="Description"
            placeholder="Optional"
            {...form.getInputProps("description")}
          />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Create</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

// ─── GeometryList ─────────────────────────────────────────────────────────────

export function GeometryList() {
  const user = useAuthStore((s) => s.user);
  const [uploadOpened, { open: openUpload, close: closeUpload }] = useDisclosure(false);
  const [linkOpened, { open: openLink, close: closeLink }] = useDisclosure(false);
  const [folderCreateOpened, { open: openFolderCreate, close: closeFolderCreate }] = useDisclosure(false);

  const queryClient = useQueryClient();

  const { data: folders = [], isLoading: foldersLoading } = useQuery({
    queryKey: ["geometry-folders"],
    queryFn: foldersApi.list,
  });

  const { data: geometries = [], isLoading: geosLoading, refetch } = useQuery({
    queryKey: ["geometries"],
    queryFn: geometriesApi.list,
    refetchInterval: (query) => {
      const data = query.state.data as GeometryResponse[] | undefined;
      const hasPending = data?.some(
        (g) => g.status === "pending" || g.status === "analyzing" || g.status === "ready-decimating"
      );
      return hasPending ? 3000 : false;
    },
  });

  const deleteFolderMutation = useMutation({
    mutationFn: (id: string) => foldersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["geometry-folders"] });
      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      notifications.show({ message: "Folder deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const isLoading = foldersLoading || geosLoading;

  const canDeleteFn = (g: GeometryResponse) =>
    !!(user && (user.id === g.uploaded_by || user.is_admin));

  function handleDeleteFolder(id: string) {
    if (!window.confirm("Delete this folder? Geometries inside will become uncategorized.")) return;
    deleteFolderMutation.mutate(id);
  }

  // Group geometries by folder_id
  const byFolder = new Map<string | null, GeometryResponse[]>();
  byFolder.set(null, []);
  for (const f of folders) byFolder.set(f.id, []);
  for (const g of geometries) {
    const key = g.folder_id ?? null;
    if (!byFolder.has(key)) byFolder.set(key, []);
    byFolder.get(key)!.push(g);
  }

  const uncategorized = byFolder.get(null) ?? [];

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="xl" fw={600}>Geometries</Text>
        <Group gap="xs">
          <Tooltip label="Refresh">
            <ActionIcon variant="subtle" onClick={() => refetch()} loading={isLoading}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Button
            variant="default"
            leftSection={<IconFolderPlus size={16} />}
            onClick={openFolderCreate}
          >
            New Folder
          </Button>
          <Button variant="default" leftSection={<IconLink size={16} />} onClick={openLink}>
            Link STL
          </Button>
          <Button leftSection={<IconUpload size={16} />} onClick={openUpload}>
            Upload STL
          </Button>
        </Group>
      </Group>

      {geometries.length === 0 && folders.length === 0 && !isLoading ? (
        <Text c="dimmed" ta="center" py="xl">
          No geometries yet. Upload an STL file to get started.
        </Text>
      ) : (
        <Stack gap="sm">
          {folders.map((folder) => (
            <FolderSection
              key={folder.id}
              folder={folder}
              geometries={byFolder.get(folder.id) ?? []}
              canDeleteFn={canDeleteFn}
              folders={folders}
              canDeleteFolder={!!(user?.is_admin)}
              onDeleteFolder={handleDeleteFolder}
            />
          ))}

          {uncategorized.length > 0 && (
            <>
              {folders.length > 0 && <Divider />}
              <FolderSection
                folder={null}
                geometries={uncategorized}
                canDeleteFn={canDeleteFn}
                folders={folders}
                canDeleteFolder={false}
                onDeleteFolder={() => {}}
              />
            </>
          )}
        </Stack>
      )}

      <GeometryUploadModal opened={uploadOpened} onClose={closeUpload} />
      <GeometryLinkModal opened={linkOpened} onClose={closeLink} />
      <FolderCreateModal opened={folderCreateOpened} onClose={closeFolderCreate} />
    </Stack>
  );
}
