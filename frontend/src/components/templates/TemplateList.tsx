import { useState } from "react";
import {
  Table,
  Button,
  Group,
  Badge,
  Text,
  ActionIcon,
  Tooltip,
  Stack,
  Title,
  Collapse,
  Paper,
  ThemeIcon,
  Popover,
  Select,
  Modal,
  TextInput,
  Textarea,
} from "@mantine/core";
import {
  IconPlus,
  IconTrash,
  IconVersions,
  IconGitFork,
  IconEye,
  IconEyeOff,
  IconDownload,
  IconUpload,
  IconEdit,
  IconFolder,
  IconFolderOpen,
  IconFolderPlus,
  IconChevronDown,
  IconChevronRight,
  IconArrowRight,
  IconArrowUp,
  IconArrowDown,
  IconArrowsSort,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useDisclosure } from "@mantine/hooks";
import { useForm } from "@mantine/form";
import {
  templatesApi,
  templateFoldersApi,
  type TemplateResponse,
  type TemplateFolderResponse,
} from "../../api/templates";
import { TemplateCreateModal } from "./TemplateCreateModal";
import { TemplateVersionsDrawer } from "./TemplateVersionsDrawer";
import { TemplateVersionEditModal } from "./TemplateVersionEditModal";
import { TemplateForkModal } from "./TemplateForkModal";
import { TemplateImportModal } from "./TemplateImportModal";
import { useAuthStore } from "../../stores/auth";
import { useSortedItems, type SortKey } from "../../hooks/useSortedItems";

function downloadSettingsJson(template: TemplateResponse) {
  const settings = template.active_version?.settings;
  if (!settings) return;
  const json = JSON.stringify(settings, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${template.name.replace(/\s+/g, "_")}_v${template.active_version?.version_number}_settings.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Sort header cell ────────────────────────────────────────────────────────

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
        {active ? (
          dir === "asc" ? <IconArrowUp size={12} /> : <IconArrowDown size={12} />
        ) : (
          <IconArrowsSort size={12} opacity={0.3} />
        )}
      </Group>
    </Table.Th>
  );
}

// ─── Template table (used inside each folder section) ────────────────────────

interface TemplateTableProps {
  templates: TemplateResponse[];
  folders: TemplateFolderResponse[];
  currentFolderId: string | null;
  onMoveFolder: (templateId: string, folderId: string | null) => void;
  onSelect: (t: TemplateResponse) => void;
  onEdit: (t: TemplateResponse) => void;
  onFork: (t: TemplateResponse) => void;
  onHide: (t: TemplateResponse) => void;
  onDelete: (t: TemplateResponse) => void;
  canManage: (t: TemplateResponse) => boolean;
  canDelete: (t: TemplateResponse) => boolean;
  isAdmin: boolean;
}

function TemplateTable({
  templates,
  folders,
  currentFolderId,
  onMoveFolder,
  onSelect,
  onEdit,
  onFork,
  onHide,
  onDelete,
  canManage,
  canDelete,
  isAdmin,
}: TemplateTableProps) {
  const { sorted, sort, toggle } = useSortedItems(templates as unknown as Record<string, unknown>[]) as {
    sorted: TemplateResponse[];
    sort: { key: SortKey; dir: "asc" | "desc" };
    toggle: (k: SortKey) => void;
  };

  const otherFolders = folders.filter((f) => f.id !== currentFolderId);
  const folderOptions = [
    { value: "__none__", label: "— Uncategorized" },
    ...otherFolders.map((f) => ({ value: f.id, label: f.name })),
  ];

  return (
    <Table highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <SortTh label="Name" sortKey="name" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th>Type</Table.Th>
          <Table.Th>Description</Table.Th>
          <Table.Th>Versions</Table.Th>
          <Table.Th>Active</Table.Th>
          <SortTh label="Created" sortKey="created_at" activeKey={sort.key} dir={sort.dir} onToggle={toggle} />
          <Table.Th />
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {sorted.map((t) => (
          <Table.Tr key={t.id} opacity={t.is_hidden ? 0.5 : 1}>
            <Table.Td>
              <Group gap="xs">
                {t.name}
                {t.is_hidden && (
                  <Badge size="xs" color="gray" variant="filled">Hidden</Badge>
                )}
              </Group>
            </Table.Td>
            <Table.Td>
              <Badge variant="light" color={t.sim_type === "aero" ? "blue" : "violet"}>
                {t.sim_type.toUpperCase()}
              </Badge>
            </Table.Td>
            <Table.Td>{t.description ?? "—"}</Table.Td>
            <Table.Td>{t.version_count}</Table.Td>
            <Table.Td>{t.active_version ? `v${t.active_version.version_number}` : "—"}</Table.Td>
            <Table.Td>{t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}</Table.Td>
            <Table.Td>
              <Group gap="xs" justify="flex-end">
                <Tooltip label="Versions">
                  <ActionIcon variant="subtle" onClick={() => onSelect(t)}>
                    <IconVersions size={16} />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label="Fork">
                  <ActionIcon variant="subtle" color="teal" onClick={() => onFork(t)}>
                    <IconGitFork size={16} />
                  </ActionIcon>
                </Tooltip>
                {t.active_version && (
                  <Tooltip label="Export active version as JSON">
                    <ActionIcon variant="subtle" color="blue" onClick={() => downloadSettingsJson(t)}>
                      <IconDownload size={16} />
                    </ActionIcon>
                  </Tooltip>
                )}
                {t.active_version && canManage(t) && (
                  <Tooltip label="Edit active version settings">
                    <ActionIcon variant="subtle" color="indigo" onClick={() => onEdit(t)}>
                      <IconEdit size={16} />
                    </ActionIcon>
                  </Tooltip>
                )}
                {/* Move to folder */}
                <Popover position="left" withArrow>
                  <Popover.Target>
                    <Tooltip label="Move to folder">
                      <ActionIcon variant="subtle" color="gray">
                        <IconArrowRight size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Popover.Target>
                  <Popover.Dropdown>
                    <Select
                      size="xs"
                      placeholder="Select folder…"
                      data={folderOptions}
                      onChange={(v) => {
                        if (v === null) return;
                        onMoveFolder(t.id, v === "__none__" ? null : v);
                      }}
                    />
                  </Popover.Dropdown>
                </Popover>
                {isAdmin && (
                  <Tooltip label={t.is_hidden ? "Show template" : "Hide template"}>
                    <ActionIcon
                      variant="subtle"
                      color={t.is_hidden ? "gray" : "orange"}
                      onClick={() => onHide(t)}
                    >
                      {t.is_hidden ? <IconEye size={16} /> : <IconEyeOff size={16} />}
                    </ActionIcon>
                  </Tooltip>
                )}
                {canDelete(t) && (
                  <Tooltip label="Delete">
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      onClick={() => onDelete(t)}
                    >
                      <IconTrash size={16} />
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

// ─── Folder section ───────────────────────────────────────────────────────────

interface FolderSectionProps {
  folder: TemplateFolderResponse | null;
  templates: TemplateResponse[];
  allFolders: TemplateFolderResponse[];
  onDeleteFolder?: () => void;
  onMoveFolder: (templateId: string, folderId: string | null) => void;
  onSelect: (t: TemplateResponse) => void;
  onEdit: (t: TemplateResponse) => void;
  onFork: (t: TemplateResponse) => void;
  onHide: (t: TemplateResponse) => void;
  onDelete: (t: TemplateResponse) => void;
  canManage: (t: TemplateResponse) => boolean;
  canDelete: (t: TemplateResponse) => boolean;
  isAdmin: boolean;
}

function FolderSection({
  folder,
  templates,
  allFolders,
  onDeleteFolder,
  onMoveFolder,
  onSelect,
  onEdit,
  onFork,
  onHide,
  onDelete,
  canManage,
  canDelete,
  isAdmin,
}: FolderSectionProps) {
  const [open, setOpen] = useState(true);
  const label = folder ? folder.name : "Uncategorized";
  const icon = open ? <IconFolderOpen size={16} /> : <IconFolder size={16} />;

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
          <Badge size="xs" variant="light" color="gray">{templates.length}</Badge>
        </Group>
        <Group gap="xs" onClick={(e) => e.stopPropagation()}>
          {folder && onDeleteFolder && (
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
        {templates.length === 0 ? (
          <Text size="xs" c="dimmed" px="sm" pb="xs">No templates in this folder.</Text>
        ) : (
          <TemplateTable
            templates={templates}
            folders={allFolders}
            currentFolderId={folder?.id ?? null}
            onMoveFolder={onMoveFolder}
            onSelect={onSelect}
            onEdit={onEdit}
            onFork={onFork}
            onHide={onHide}
            onDelete={onDelete}
            canManage={canManage}
            canDelete={canDelete}
            isAdmin={isAdmin}
          />
        )}
      </Collapse>
    </Paper>
  );
}

// ─── New Folder modal ─────────────────────────────────────────────────────────

function NewFolderModal({
  opened,
  onClose,
}: { opened: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const form = useForm({ initialValues: { name: "", description: "" } });
  const mutation = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      templateFoldersApi.create({ name: data.name, description: data.description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templateFolders"] });
      notifications.show({ message: "Folder created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });
  return (
    <Modal opened={opened} onClose={onClose} title="New Template Folder" size="sm">
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack gap="sm">
          <TextInput label="Name" required {...form.getInputProps("name")} />
          <Textarea label="Description" autosize minRows={2} {...form.getInputProps("description")} />
          <Button type="submit" loading={mutation.isPending}>Create</Button>
        </Stack>
      </form>
    </Modal>
  );
}

// ─── Main TemplateList ────────────────────────────────────────────────────────

export function TemplateList() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [newFolderOpen, setNewFolderOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateResponse | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<TemplateResponse | null>(null);
  const [forkTarget, setForkTarget] = useState<TemplateResponse | null>(null);

  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: templatesApi.list,
  });

  const { data: folders = [] } = useQuery({
    queryKey: ["templateFolders"],
    queryFn: templateFoldersApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const hideMutation = useMutation({
    mutationFn: ({ id, is_hidden }: { id: string; is_hidden: boolean }) =>
      templatesApi.setHidden(id, is_hidden),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({
        message: vars.is_hidden ? "Template hidden" : "Template visible",
        color: "blue",
      });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const moveFolderMutation = useMutation({
    mutationFn: ({ id, folderId }: { id: string; folderId: string | null }) =>
      templatesApi.updateFolder(id, folderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["templates"] }),
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const deleteFolderMutation = useMutation({
    mutationFn: (folderId: string) => templateFoldersApi.delete(folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templateFolders"] });
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Folder deleted", color: "green" });
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const canDelete = (t: TemplateResponse) => user?.id === t.created_by || !!user?.is_admin;
  const canManage = (t: TemplateResponse) => user?.id === t.created_by || !!user?.is_admin;

  const handleMove = (templateId: string, folderId: string | null) =>
    moveFolderMutation.mutate({ id: templateId, folderId });

  // Group by folder
  const byFolder = new Map<string | null, TemplateResponse[]>();
  byFolder.set(null, []);
  for (const f of folders) byFolder.set(f.id, []);
  for (const t of templates) {
    const key = t.folder_id ?? null;
    if (!byFolder.has(key)) byFolder.set(null, [...(byFolder.get(null) ?? [])]);
    byFolder.get(key)!.push(t);
    if (key !== null && !byFolder.has(key)) {
      byFolder.get(null)!.push(t); // safety: orphan → uncategorized
    }
  }

  const sharedProps = {
    allFolders: folders,
    onMoveFolder: handleMove,
    onSelect: setSelectedTemplate,
    onEdit: setEditingTemplate,
    onFork: setForkTarget,
    onHide: (t: TemplateResponse) => hideMutation.mutate({ id: t.id, is_hidden: !t.is_hidden }),
    onDelete: (t: TemplateResponse) => {
      if (confirm(`Delete "${t.name}"?`)) deleteMutation.mutate(t.id);
    },
    canManage,
    canDelete,
    isAdmin: !!user?.is_admin,
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Templates</Title>
        <Group gap="xs">
          <Button
            variant="outline"
            leftSection={<IconFolderPlus size={16} />}
            onClick={() => setNewFolderOpen(true)}
          >
            New Folder
          </Button>
          <Button
            variant="outline"
            leftSection={<IconUpload size={16} />}
            onClick={() => setImportOpen(true)}
          >
            Import from JSON
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={() => setCreateOpen(true)}>
            New Template
          </Button>
        </Group>
      </Group>

      {/* Folder sections */}
      {folders.map((f) => (
        <FolderSection
          key={f.id}
          folder={f}
          templates={byFolder.get(f.id) ?? []}
          onDeleteFolder={() => {
            if (confirm(`Delete folder "${f.name}"? Templates will become uncategorized.`))
              deleteFolderMutation.mutate(f.id);
          }}
          {...sharedProps}
        />
      ))}

      {/* Uncategorized */}
      <FolderSection
        key="__uncategorized__"
        folder={null}
        templates={byFolder.get(null) ?? []}
        {...sharedProps}
      />

      <NewFolderModal opened={newFolderOpen} onClose={() => setNewFolderOpen(false)} />

      <TemplateCreateModal opened={createOpen} onClose={() => setCreateOpen(false)} />
      <TemplateImportModal opened={importOpen} onClose={() => setImportOpen(false)} />

      {selectedTemplate && (
        <TemplateVersionsDrawer
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}
      {forkTarget && (
        <TemplateForkModal opened source={forkTarget} onClose={() => setForkTarget(null)} />
      )}
      {editingTemplate?.active_version && (
        <TemplateVersionEditModal
          opened
          onClose={() => setEditingTemplate(null)}
          template={editingTemplate}
          version={editingTemplate.active_version}
        />
      )}
    </Stack>
  );
}


