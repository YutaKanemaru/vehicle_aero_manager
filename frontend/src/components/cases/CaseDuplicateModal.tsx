import { Modal, TextInput, Textarea, Button, Stack, Group, Text, Badge } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { casesApi, type CaseResponse, type CaseDuplicateRequest } from "../../api/configurations";

interface Props {
  opened: boolean;
  onClose: () => void;
  sourceCase: CaseResponse;
}

export function CaseDuplicateModal({ opened, onClose, sourceCase }: Props) {
  const queryClient = useQueryClient();

  const form = useForm<CaseDuplicateRequest>({
    initialValues: {
      name: `${sourceCase.name} (copy)`,
      description: sourceCase.description ?? "",
    },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CaseDuplicateRequest) => casesApi.duplicate(sourceCase.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case duplicated", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="Duplicate Case" size="sm">
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack>
          <Text size="sm" c="dimmed">
            Creates a new Case with the same Template, Assembly, and Condition Map as{" "}
            <Badge variant="outline" size="sm">{sourceCase.case_number || sourceCase.name}</Badge>.
            Runs are not copied.
          </Text>
          <TextInput
            label="New Case Name"
            placeholder="e.g. AUR_v2.5_EXT_copy"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            rows={2}
            {...form.getInputProps("description")}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Duplicate</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
