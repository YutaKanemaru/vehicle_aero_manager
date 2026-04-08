import {
  Modal,
  TextInput,
  Textarea,
  Button,
  Group,
  Stack,
  Select,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { assembliesApi, type AssemblyCreate } from "../../api/geometries";
import { templatesApi } from "../../api/templates";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function AssemblyCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();

  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: templatesApi.list,
  });

  const form = useForm<AssemblyCreate>({
    initialValues: { name: "", description: null, template_id: null },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: AssemblyCreate) => assembliesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assemblies"] });
      notifications.show({ message: "Assembly created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  const templateOptions = templates.map((t) => ({
    value: t.id,
    label: `${t.name} (${t.sim_type.toUpperCase()})`,
  }));

  return (
    <Modal opened={opened} onClose={onClose} title="Create Assembly" size="md">
      <form
        onSubmit={form.onSubmit((values) =>
          mutation.mutate({
            name: values.name.trim(),
            description: values.description || null,
            template_id: values.template_id || null,
          })
        )}
      >
        <Stack>
          <TextInput
            label="Name"
            placeholder="e.g. AUR_v1.2_assembly"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            {...form.getInputProps("description")}
          />
          <Select
            label="Link to template (optional)"
            placeholder="Select template"
            clearable
            data={templateOptions}
            {...form.getInputProps("template_id")}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Create</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
