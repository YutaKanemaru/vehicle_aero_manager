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
} from "@mantine/core";
import { IconPlus, IconTrash, IconVersions, IconGitFork } from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateResponse } from "../../api/templates";
import { TemplateCreateModal } from "./TemplateCreateModal";
import { TemplateVersionsDrawer } from "./TemplateVersionsDrawer";
import { TemplateForkModal } from "./TemplateForkModal";
import { useAuthStore } from "../../stores/auth";

export function TemplateList() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateResponse | null>(null);
  const [forkTarget, setForkTarget] = useState<TemplateResponse | null>(null);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: templatesApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template deleted", color: "green" });
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  const canDelete = (t: TemplateResponse) =>
    user?.id === t.created_by || user?.is_admin;

  const rows = templates.map((t) => (
    <Table.Tr key={t.id}>
      <Table.Td>{t.name}</Table.Td>
      <Table.Td>
        <Badge variant="light" color={t.sim_type === "aero" ? "blue" : "violet"}>
          {t.sim_type.toUpperCase()}
        </Badge>
      </Table.Td>
      <Table.Td>{t.description ?? "—"}</Table.Td>
      <Table.Td>{t.version_count}</Table.Td>
      <Table.Td>
        {t.active_version ? `v${t.active_version.version_number}` : "—"}
      </Table.Td>
      <Table.Td>
        <Group gap="xs" justify="flex-end">
          <Tooltip label="Versions">
              <ActionIcon
                variant="subtle"
                onClick={() => setSelectedTemplate(t)}
              >
                <IconVersions size={16} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Fork">
              <ActionIcon
                variant="subtle"
                color="teal"
                onClick={() => setForkTarget(t)}
              >
                <IconGitFork size={16} />
              </ActionIcon>
            </Tooltip>
          {canDelete(t) && (
            <Tooltip label="Delete">
              <ActionIcon
                variant="subtle"
                color="red"
                loading={deleteMutation.isPending}
                onClick={() => {
                  if (confirm(`Delete "${t.name}"?`)) deleteMutation.mutate(t.id);
                }}
              >
                <IconTrash size={16} />
              </ActionIcon>
            </Tooltip>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Templates</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setCreateOpen(true)}>
          New Template
        </Button>
      </Group>

      {isLoading ? (
        <Text c="dimmed">Loading…</Text>
      ) : templates.length === 0 ? (
        <Text c="dimmed">No templates yet. Create one to get started.</Text>
      ) : (
        <Table striped highlightOnHover withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Description</Table.Th>
              <Table.Th>Versions</Table.Th>
              <Table.Th>Active</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>{rows}</Table.Tbody>
        </Table>
      )}

      <TemplateCreateModal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
      />

      {selectedTemplate && (
        <TemplateVersionsDrawer
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}

      {forkTarget && (
        <TemplateForkModal
          opened
          source={forkTarget}
          onClose={() => setForkTarget(null)}
        />
      )}
    </Stack>
  );
}
