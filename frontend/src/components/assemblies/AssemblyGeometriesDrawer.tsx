import {
  Drawer,
  Text,
  Stack,
  Group,
  Badge,
  ActionIcon,
  Tooltip,
  Box,
  Checkbox,
  Button,
  ScrollArea,
  Alert,
  SegmentedControl,
  Paper,
  Collapse,
  UnstyledButton,
} from "@mantine/core";
import {
  IconTrash,
  IconPlus,
  IconAlertCircle,
  IconFolder,
  IconFolderOpen,
  IconChevronDown,
  IconChevronRight,
} from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useState } from "react";
import { useDisclosure } from "@mantine/hooks";
import {
  assembliesApi,
  geometriesApi,
  foldersApi,
  type AssemblyResponse,
  type GeometryResponse,
  type GeometryFolderResponse,
} from "../../api/geometries";

// ── helpers ───────────────────────────────────────────────────────────────────

function statusColor(status: string) {
  if (status === "ready") return "green";
  if (status === "error") return "red";
  if (status === "analyzing") return "blue";
  if (status === "ready-decimating") return "violet";
  return "yellow";
}

// ── FolderBlock ───────────────────────────────────────────────────────────────

interface FolderBlockProps {
  label: string;
  geometries: GeometryResponse[];
  selected: Set<string>;
  onToggle: (id: string, checked: boolean) => void;
}

function FolderBlock({ label, geometries, selected, onToggle }: FolderBlockProps) {
  const [opened, { toggle }] = useDisclosure(true);

  if (geometries.length === 0) return null;

  const allChecked = geometries.every((g) => selected.has(g.id));
  const someChecked = geometries.some((g) => selected.has(g.id)) && !allChecked;

  function toggleAll(checked: boolean) {
    geometries.forEach((g) => onToggle(g.id, checked));
  }

  return (
    <Paper withBorder p={0} style={{ overflow: "hidden" }}>
      <UnstyledButton onClick={toggle} style={{ width: "100%", padding: "6px 10px" }}>
        <Group gap="xs" wrap="nowrap">
          {opened ? (
            <IconFolderOpen size={14} color="var(--mantine-color-yellow-6)" />
          ) : (
            <IconFolder size={14} color="var(--mantine-color-yellow-6)" />
          )}
          <Checkbox
            size="xs"
            checked={allChecked}
            indeterminate={someChecked}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => toggleAll(e.currentTarget.checked)}
          />
          <Text size="sm" fw={500} style={{ flex: 1 }}>
            {label}
          </Text>
          <Badge size="xs" variant="light" color="gray">
            {geometries.length}
          </Badge>
          {opened ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}
        </Group>
      </UnstyledButton>
      <Collapse in={opened}>
        <Stack gap={0}>
          {geometries.map((g) => (
            <Group
              key={g.id}
              gap="xs"
              px="sm"
              py={5}
              style={{ borderTop: "1px solid var(--mantine-color-default-border)" }}
            >
              <Checkbox
                size="xs"
                checked={selected.has(g.id)}
                onChange={(e) => onToggle(g.id, e.currentTarget.checked)}
              />
              <Box style={{ flex: 1, minWidth: 0 }}>
                <Text size="sm" truncate>{g.name}</Text>
                <Text size="xs" c="dimmed" truncate>{g.original_filename}</Text>
              </Box>
            </Group>
          ))}
        </Stack>
      </Collapse>
    </Paper>
  );
}

// ── CurrentPanel ──────────────────────────────────────────────────────────────

interface CurrentPanelProps {
  assembly: AssemblyResponse;
  removeMutation: ReturnType<typeof useMutation<void, Error, string>>;
}

function CurrentPanel({ assembly, removeMutation }: CurrentPanelProps) {
  const geometries = (assembly.geometries ?? []) as GeometryResponse[];

  if (geometries.length === 0) {
    return <Text size="sm" c="dimmed">No geometries assigned yet.</Text>;
  }

  return (
    <Stack gap={4}>
      {geometries.map((g) => (
        <Group
          key={g.id}
          justify="space-between"
          p="xs"
          style={{ border: "1px solid var(--mantine-color-default-border)", borderRadius: 6 }}
        >
          <Box style={{ minWidth: 0, flex: 1 }}>
            <Text size="sm" truncate>{g.name}</Text>
            <Group gap={6}>
              <Badge color={statusColor(g.status)} size="xs">{g.status}</Badge>
              <Text size="xs" c="dimmed" truncate>{g.original_filename}</Text>
            </Group>
          </Box>
          <Tooltip label="Remove">
            <ActionIcon
              color="red"
              variant="subtle"
              size="sm"
              loading={removeMutation.isPending && (removeMutation.variables as string) === g.id}
              onClick={() => removeMutation.mutate(g.id)}
            >
              <IconTrash size={14} />
            </ActionIcon>
          </Tooltip>
        </Group>
      ))}
    </Stack>
  );
}

// ── AddPanel ──────────────────────────────────────────────────────────────────

interface AddPanelProps {
  available: GeometryResponse[];
  folders: GeometryFolderResponse[];
  selected: Set<string>;
  onToggle: (id: string, checked: boolean) => void;
  onAdd: () => void;
  isPending: boolean;
}

function AddPanel({ available, folders, selected, onToggle, onAdd, isPending }: AddPanelProps) {
  if (available.length === 0) {
    return (
      <Alert icon={<IconAlertCircle size={14} />} color="gray">
        No ready geometries available to add.
      </Alert>
    );
  }

  const byFolder = new Map<string | null, GeometryResponse[]>();
  byFolder.set(null, []);
  folders.forEach((f) => byFolder.set(f.id, []));
  available.forEach((g) => {
    const key = g.folder_id ?? null;
    if (!byFolder.has(key)) byFolder.set(key, []);
    byFolder.get(key)!.push(g);
  });

  const hasAnyFolder = folders.some((f) => (byFolder.get(f.id)?.length ?? 0) > 0);

  return (
    <Stack gap="xs" style={{ height: "100%", overflow: "hidden", display: "flex", flexDirection: "column" }}>
      <ScrollArea style={{ flex: 1 }} type="auto">
        <Stack gap="xs">
          {folders.map((f) => (
            <FolderBlock
              key={f.id}
              label={f.name}
              geometries={byFolder.get(f.id) ?? []}
              selected={selected}
              onToggle={onToggle}
            />
          ))}
          {(byFolder.get(null)?.length ?? 0) > 0 && (
            hasAnyFolder ? (
              <FolderBlock
                label="Uncategorized"
                geometries={byFolder.get(null) ?? []}
                selected={selected}
                onToggle={onToggle}
              />
            ) : (
              <Stack gap={4}>
                {(byFolder.get(null) ?? []).map((g) => (
                  <Group
                    key={g.id}
                    gap="xs"
                    p="xs"
                    style={{ border: "1px solid var(--mantine-color-default-border)", borderRadius: 6 }}
                  >
                    <Checkbox
                      size="xs"
                      checked={selected.has(g.id)}
                      onChange={(e) => onToggle(g.id, e.currentTarget.checked)}
                    />
                    <Box style={{ flex: 1, minWidth: 0 }}>
                      <Text size="sm" truncate>{g.name}</Text>
                      <Text size="xs" c="dimmed" truncate>{g.original_filename}</Text>
                    </Box>
                  </Group>
                ))}
              </Stack>
            )
          )}
        </Stack>
      </ScrollArea>
      <Group justify="flex-end" pt="xs" style={{ borderTop: "1px solid var(--mantine-color-default-border)" }}>
        <Button
          leftSection={<IconPlus size={14} />}
          size="xs"
          disabled={selected.size === 0}
          loading={isPending}
          onClick={onAdd}
        >
          Add selected ({selected.size})
        </Button>
      </Group>
    </Stack>
  );
}

// ── Main drawer ───────────────────────────────────────────────────────────────

interface Props {
  assembly: AssemblyResponse | null;
  opened: boolean;
  onClose: () => void;
}

export function AssemblyGeometriesDrawer({ assembly, opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<string>("current");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: allGeometries = [] } = useQuery({
    queryKey: ["geometries"],
    queryFn: geometriesApi.list,
    enabled: opened,
  });

  const { data: folders = [] } = useQuery<GeometryFolderResponse[]>({
    queryKey: ["geometry-folders"],
    queryFn: foldersApi.list,
    enabled: opened,
  });

  const assemblyGeometryIds = new Set((assembly?.geometries ?? []).map((g) => g.id));
  const available = (allGeometries as GeometryResponse[]).filter(
    (g) => !assemblyGeometryIds.has(g.id) && g.status === "ready"
  );

  const addMutation = useMutation({
    mutationFn: (geometryId: string) => assembliesApi.addGeometry(assembly!.id, geometryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["assemblies"] }),
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

  function handleToggle(id: string, checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      checked ? next.add(id) : next.delete(id);
      return next;
    });
  }

  function handleAdd() {
    const ids = [...selected];
    let remaining = ids.length;
    ids.forEach((id) => {
      addMutation.mutate(id, {
        onSuccess: () => {
          remaining--;
          if (remaining === 0) {
            setSelected(new Set());
            notifications.show({
              message: `${ids.length} geometry${ids.length > 1 ? " geometries" : ""} added`,
              color: "green",
            });
          }
        },
      });
    });
  }

  if (!assembly) return null;

  const currentCount = (assembly.geometries ?? []).length;

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title={<Text fw={600}>Geometries \u2014 {assembly.name}</Text>}
      position="right"
      size="md"
      styles={{
        body: {
          display: "flex",
          flexDirection: "column",
          height: "calc(100% - 60px)",
          padding: "12px 16px",
          gap: 12,
        },
      }}
    >
      <SegmentedControl
        value={tab}
        onChange={setTab}
        data={[
          { value: "current", label: `Current (${currentCount})` },
          { value: "add", label: "Add geometries" },
        ]}
        fullWidth
        size="sm"
      />

      <Box style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        {tab === "current" ? (
          <ScrollArea style={{ flex: 1 }} type="auto">
            <CurrentPanel assembly={assembly} removeMutation={removeMutation} />
          </ScrollArea>
        ) : (
          <AddPanel
            available={available}
            folders={folders}
            selected={selected}
            onToggle={handleToggle}
            onAdd={handleAdd}
            isPending={addMutation.isPending}
          />
        )}
      </Box>
    </Drawer>
  );
}
