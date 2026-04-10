import {
  Modal,
  TextInput,
  Textarea,
  Button,
  Stack,
  Group,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { mapsApi, type ConditionMapCreate } from "../../api/configurations";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function MapCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();

  const form = useForm<ConditionMapCreate>({
    initialValues: { name: "", description: "" },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ConditionMapCreate) => mapsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maps"] });
      notifications.show({ message: "Condition Map created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="New Condition Map" size="md">
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="e.g. Baseline Conditions"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            rows={2}
            {...form.getInputProps("description")}
          />
          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              Create
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
