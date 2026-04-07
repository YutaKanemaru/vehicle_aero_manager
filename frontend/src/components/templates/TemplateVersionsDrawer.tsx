import {
  Drawer,
  Stack,
  Group,
  Text,
  Badge,
  Button,
  Textarea,
  Divider,
  Title,
  ActionIcon,
  Tooltip,
} from "@mantine/core";
import { IconCheck } from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateResponse } from "../../api/templates";
import { useAuthStore } from "../../stores/auth";

interface Props {
  template: TemplateResponse;
  onClose: () => void;
}

export function TemplateVersionsDrawer({ template, onClose }: Props) {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const { data: versions = [], isLoading } = useQuery({
    queryKey: ["templates", template.id, "versions"],
    queryFn: () => templatesApi.listVersions(template.id),
  });

  const canManage = user?.id === template.created_by || user?.is_admin;

  const activateMutation = useMutation({
    mutationFn: (versionId: string) =>
      templatesApi.activateVersion(template.id, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      queryClient.invalidateQueries({ queryKey: ["templates", template.id, "versions"] });
      notifications.show({ message: "Version activated", color: "green" });
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  return (
    <Drawer
      opened
      onClose={onClose}
      title={
        <Group gap="sm">
          <Title order={4}>{template.name}</Title>
          <Badge variant="light" color={template.sim_type === "aero" ? "blue" : "violet"}>
            {template.sim_type.toUpperCase()}
          </Badge>
        </Group>
      }
      position="right"
      size="md"
    >
      <Stack>
        {template.description && (
          <Text size="sm" c="dimmed">{template.description}</Text>
        )}
        <Divider label="Version history" labelPosition="left" />

        {isLoading && <Text c="dimmed">Loading…</Text>}

        {versions
          .slice()
          .reverse()
          .map((v) => (
            <Stack key={v.id} gap="xs" p="sm" style={{ border: "1px solid var(--mantine-color-default-border)", borderRadius: 8 }}>
              <Group justify="space-between">
                <Group gap="xs">
                  <Text fw={600}>v{v.version_number}</Text>
                  {v.is_active && (
                    <Badge color="green" size="sm">Active</Badge>
                  )}
                </Group>
                {canManage && !v.is_active && (
                  <Tooltip label="Set as active">
                    <ActionIcon
                      variant="subtle"
                      color="green"
                      loading={activateMutation.isPending}
                      onClick={() => activateMutation.mutate(v.id)}
                    >
                      <IconCheck size={16} />
                    </ActionIcon>
                  </Tooltip>
                )}
              </Group>

              {v.comment && (
                <Text size="sm" c="dimmed">{v.comment}</Text>
              )}
              <Text size="xs" c="dimmed">
                {new Date(v.created_at).toLocaleString()}
              </Text>
            </Stack>
          ))}
      </Stack>
    </Drawer>
  );
}
