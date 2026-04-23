import {
  Table,
  Button,
  Group,
  Text,
  Stack,
  ActionIcon,
  Tooltip,
  Badge,
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
  IconCopy,
  IconArrowsLeftRight,
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
import { useNavigate } from "react-router-dom";
import { useDisclosure } from "@mantine/hooks";
import { useForm } from "@mantine/form";
import {
  casesApi,
  caseFoldersApi,
  type CaseResponse,
  type CaseFolderResponse,
} from "../../api/configurations";
import { useAuthStore } from "../../stores/auth";
import { CaseCreateModal } from "./CaseCreateModal";
import { CaseDuplicateModal } from "./CaseDuplicateModal";
import { CaseCompareModal } from "./CaseCompareModal";
import { useSortedItems, type SortKey } from "../../hooks/useSortedItems";

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

// ── CaseTable (inside folder) ─────────────────────────────────────────────────

function CaseTable({
  cases,
  onRowClick,
  onDelete,
  onDuplicate,
  onMoveFolder,
  folders,
  canDeleteFn,
  deletingId,
  compareMode,
  selectedForCompare,
  toggleCompareSelect,
}: {
  cases: CaseResponse[];
  onRowClick: (c: CaseResponse) => void;
  onDelete: (c: CaseResponse) => void;
  onDuplicate: (c: CaseResponse) => void;
  onMoveFolder: (caseId: string, folderId: string | null) => void;
  folders: CaseFolderResponse[];
  canDeleteFn: (c: CaseResponse) => boolean;
  deletingId: string | undefined;
  compareMode: boolean;
  selectedForCompare: string[];
  toggleCompareSelect: (id: string) => void;
}) {
  const { sorted, sort, toggle } = useSortedItems(
    cases as unknown as Record<string, unknown>[]
  ) as { sorted: CaseResponse[]; sort: { key: SortKey; dir: "asc" | "desc" }; toggle: (k: SortKey) => void };

  if (cases.length === 0) {
    return <Text size="xs" c="dimmed" px="sm" pb="xs">No cases in this folder.</Text>;
  }

  return (
    <Table striped highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <Table.Th style={{ width: 70 }}>#</Table.Th>
          <SortTh label="Name" sortKey="name" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th>Template</Table.Th>
          <Table.Th>Assembly</Table.Th>
          <Table.Th>Map</Table.Th>
          <Table.Th style={{ width: 60 }}>Runs</Table.Th>
          <SortTh label="Created" sortKey="created_at" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th />
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {sorted.map((c) => (
          <Table.Tr
            key={c.id}
            style={{
              cursor: "pointer",
              background: compareMode && selectedForCompare.includes(c.id)
                ? "rgba(255,140,0,0.12)"
                : undefined,
            }}
            onClick={() => compareMode ? toggleCompareSelect(c.id) : onRowClick(c)}
          >
            <Table.Td>
              <Badge variant="outline" color="gray" size="sm">{c.case_number || "—"}</Badge>
            </Table.Td>
            <Table.Td>
              <Text fw={500} size="sm">{c.name}</Text>
              {c.description && (
                <Text size="xs" c="dimmed" lineClamp={1}>{c.description}</Text>
              )}
            </Table.Td>
            <Table.Td>
              <Badge variant="light" color="violet" size="sm">
                {c.template_name || c.template_id.slice(0, 8)}
              </Badge>
            </Table.Td>
            <Table.Td>
              <Badge variant="light" color="teal" size="sm">
                {c.assembly_name || c.assembly_id.slice(0, 8)}
              </Badge>
            </Table.Td>
            <Table.Td>
              {c.map_id ? (
                <Badge variant="dot" color="cyan" size="sm">
                  {c.map_name || c.map_id.slice(0, 8)}
                </Badge>
              ) : (
                <Text size="xs" c="dimmed">—</Text>
              )}
            </Table.Td>
            <Table.Td><Text size="sm">{c.run_count ?? 0}</Text></Table.Td>
            <Table.Td>
              <Text size="xs" c="dimmed">{new Date(c.created_at).toLocaleDateString()}</Text>
            </Table.Td>
            <Table.Td onClick={(e) => e.stopPropagation()}>
              <Group gap={4} wrap="nowrap">
                <Tooltip label="Open runs">
                  <ActionIcon size="sm" variant="subtle" color="blue" onClick={() => onRowClick(c)}>
                    <IconSettings size={14} />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Duplicate">
                  <ActionIcon size="sm" variant="subtle" color="orange" onClick={() => onDuplicate(c)}>
                    <IconCopy size={14} />
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
                      value={c.folder_id ?? null}
                      onChange={(v) => onMoveFolder(c.id, v)}
                    />
                  </Popover.Dropdown>
                </Popover>
                {canDeleteFn(c) && (
                  <Tooltip label="Delete">
                    <ActionIcon
                      size="sm"
                      variant="subtle"
                      color="red"
                      loading={deletingId === c.id}
                      onClick={() => onDelete(c)}
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
  cases,
  onRowClick,
  onDelete,
  onDuplicate,
  onMoveFolder,
  folders,
  canDeleteFn,
  deletingId,
  canDeleteFolder,
  onDeleteFolder,
  compareMode,
  selectedForCompare,
  toggleCompareSelect,
}: {
  folder: CaseFolderResponse | null;
  cases: CaseResponse[];
  onRowClick: (c: CaseResponse) => void;
  onDelete: (c: CaseResponse) => void;
  onDuplicate: (c: CaseResponse) => void;
  onMoveFolder: (caseId: string, folderId: string | null) => void;
  folders: CaseFolderResponse[];
  canDeleteFn: (c: CaseResponse) => boolean;
  deletingId: string | undefined;
  canDeleteFolder: boolean;
  onDeleteFolder: (id: string) => void;
  compareMode: boolean;
  selectedForCompare: string[];
  toggleCompareSelect: (id: string) => void;
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
            {opened ? <IconFolderOpen size={14} /> : <IconFolder size={14} />}
          </ThemeIcon>
          <Text size="sm" fw={500}>{label}</Text>
          <Badge size="xs" variant="outline" color="gray">{cases.length}</Badge>
        </Group>
        <Group gap="xs" onClick={(e) => e.stopPropagation()}>
          {folder && canDeleteFolder && (
            <Tooltip label="Delete folder">
              <ActionIcon size="xs" variant="subtle" color="red" onClick={() => onDeleteFolder(folder.id)}>
                <IconTrash size={12} />
              </ActionIcon>
            </Tooltip>
          )}
          {opened ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
        </Group>
      </Group>

      <Collapse in={opened}>
        <CaseTable
          cases={cases}
          onRowClick={onRowClick}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
          onMoveFolder={onMoveFolder}
          folders={folders}
          canDeleteFn={canDeleteFn}
          deletingId={deletingId}
          compareMode={compareMode}
          selectedForCompare={selectedForCompare}
          toggleCompareSelect={toggleCompareSelect}
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
      caseFoldersApi.create(vals),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caseFolders"] });
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

// ── CaseList ──────────────────────────────────────────────────────────────────

export function CaseList() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const [newFolderOpened, { open: openNewFolder, close: closeNewFolder }] = useDisclosure(false);
  const [duplicateCase, setDuplicateCase] = useState<CaseResponse | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);

  const { data: cases = [], isLoading, refetch } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  const { data: folders = [] } = useQuery({
    queryKey: ["caseFolders"],
    queryFn: caseFoldersApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => casesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const deleteFolderMutation = useMutation({
    mutationFn: (id: string) => caseFoldersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caseFolders"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Folder deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const moveMutation = useMutation({
    mutationFn: ({ id, folderId }: { id: string; folderId: string | null }) =>
      casesApi.updateFolder(id, folderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cases"] }),
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function openDrawer(c: CaseResponse) {
    navigate(`/cases/${c.id}`);
  }

  function handleDelete(c: CaseResponse) {
    if (confirm(`Delete case "${c.name}" and all its runs?`)) deleteMutation.mutate(c.id);
  }

  function handleDeleteFolder(id: string) {
    if (confirm("Delete folder? Cases will become uncategorized."))
      deleteFolderMutation.mutate(id);
  }

  function toggleCompareSelect(id: string) {
    setSelectedForCompare((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : prev
    );
  }

  const canDelete = (c: CaseResponse) => c.created_by === user?.id || !!user?.is_admin;

  // Group by folder
  const byFolder = new Map<string | null, CaseResponse[]>();
  byFolder.set(null, []);
  for (const f of folders) byFolder.set(f.id, []);
  for (const c of cases) {
    const key = c.folder_id ?? null;
    const list = byFolder.get(key);
    if (list) list.push(c);
    else byFolder.get(null)!.push(c);
  }

  const sharedTableProps = {
    onRowClick: openDrawer,
    onDelete: handleDelete,
    onDuplicate: (c: CaseResponse) => setDuplicateCase(c),
    onMoveFolder: (id: string, folderId: string | null) => moveMutation.mutate({ id, folderId }),
    folders,
    canDeleteFn: canDelete,
    deletingId: deleteMutation.isPending ? deleteMutation.variables ?? undefined : undefined,
    compareMode,
    selectedForCompare,
    toggleCompareSelect,
  };

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
          <Tooltip label={compareMode ? "Exit compare mode" : "Compare two cases"}>
            <ActionIcon
              variant={compareMode ? "filled" : "subtle"}
              color="orange"
              onClick={() => { setCompareMode((m) => !m); setSelectedForCompare([]); }}
            >
              <IconArrowsLeftRight size={16} />
            </ActionIcon>
          </Tooltip>
          {compareMode && selectedForCompare.length === 2 && (
            <Button size="xs" color="orange" onClick={() => setCompareOpen(true)}>
              Compare
            </Button>
          )}
          <Tooltip label="New Folder">
            <ActionIcon variant="subtle" onClick={openNewFolder}>
              <IconFolderPlus size={16} />
            </ActionIcon>
          </Tooltip>
          <Button leftSection={<IconPlus size={14} />} onClick={openCreate}>
            New Case
          </Button>
        </Group>
      </Group>

      {cases.length === 0 && folders.length === 0 && !isLoading ? (
        <Text c="dimmed" size="sm">
          No cases yet. Create a case by linking a Template and Assembly.
        </Text>
      ) : (
        <>
          {folders.map((f) => (
            <FolderSection
              key={f.id}
              folder={f}
              cases={byFolder.get(f.id) ?? []}
              canDeleteFolder={!!(user?.is_admin)}
              onDeleteFolder={handleDeleteFolder}
              {...sharedTableProps}
            />
          ))}
          <FolderSection
            key="__uncategorized__"
            folder={null}
            cases={byFolder.get(null) ?? []}
            canDeleteFolder={false}
            onDeleteFolder={() => {}}
            {...sharedTableProps}
          />
        </>
      )}

      <CaseCreateModal opened={createOpened} onClose={closeCreate} />
      <NewFolderModal opened={newFolderOpened} onClose={closeNewFolder} />

      {compareOpen && selectedForCompare.length === 2 && (
        <CaseCompareModal
          caseIds={selectedForCompare as [string, string]}
          opened={compareOpen}
          onClose={() => setCompareOpen(false)}
        />
      )}

      {duplicateCase && (
        <CaseDuplicateModal
          sourceCase={duplicateCase}
          opened={!!duplicateCase}
          onClose={() => setDuplicateCase(null)}
        />
      )}
    </Stack>
  );
}
