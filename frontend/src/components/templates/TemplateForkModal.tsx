import { Modal, TextInput, Textarea, Button, Group, Stack, Text, Badge } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateResponse, type TemplateForkRequest } from "../../api/templates";

interface Props {
  opened: boolean;
  onClose: () => void;
  source: TemplateResponse;
}

export function TemplateForkModal({ opened, onClose, source }: Props) {
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: {
      name: `${source.name}_copy`,
      description: source.description ?? "",
      comment: "",
    },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: TemplateForkRequest) => templatesApi.fork(source.id, data),
    onSuccess: (newTemplate) => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({
        message: `"${newTemplate.name}" created from "${source.name}"`,
        color: "green",
      });
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSubmit(values: typeof form.values) {
    mutation.mutate({
      name: values.name.trim(),
      description: values.description.trim() || undefined,
      comment: values.comment.trim() || undefined,
    });
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Fork Template" size="md">
      <Stack>
        <Group gap="xs">
          <Text size="sm" c="dimmed">Source:</Text>
          <Text size="sm" fw={500}>{source.name}</Text>
          <Badge variant="light" color={source.sim_type === "aero" ? "blue" : "violet"} size="sm">
            {source.sim_type.toUpperCase()}
          </Badge>
          {source.active_version && (
            <Badge variant="outline" color="gray" size="sm">
              v{source.active_version.version_number}
            </Badge>
          )}
        </Group>

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput
              label="New template name"
              placeholder="e.g. Aero_Standard_2025_v2"
              required
              {...form.getInputProps("name")}
            />
            <Textarea
              label="Description"
              placeholder="Optional description"
              {...form.getInputProps("description")}
            />
            <TextInput
              label="Version comment"
              placeholder={`Forked from '${source.name}'`}
              {...form.getInputProps("comment")}
            />
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" loading={mutation.isPending}>
                Fork
              </Button>
            </Group>
          </Stack>
        </form>
      </Stack>
    </Modal>
  );
}
