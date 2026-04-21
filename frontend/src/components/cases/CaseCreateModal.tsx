import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Switch,
  Button,
  Stack,
  Group,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { casesApi, mapsApi, type CaseCreate } from "../../api/configurations";
import { templatesApi } from "../../api/templates";
import { assembliesApi } from "../../api/geometries";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function CaseCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();

  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: templatesApi.list,
  });

  const { data: assemblies = [] } = useQuery({
    queryKey: ["assemblies"],
    queryFn: assembliesApi.list,
  });

  const { data: maps = [] } = useQuery({
    queryKey: ["maps"],
    queryFn: mapsApi.list,
  });

  const form = useForm<CaseCreate & { withRuns: boolean }>({
    initialValues: {
      name: "",
      description: "",
      template_id: "",
      assembly_id: "",
      map_id: null,
      withRuns: false,
    },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
      template_id: (v) => (v ? null : "Template is required"),
      assembly_id: (v) => (v ? null : "Assembly is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CaseCreate & { withRuns: boolean }) => {
      const { withRuns, ...caseData } = data;
      return casesApi.create(caseData, withRuns);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case created", color: "green" });
      form.reset();
      onClose();
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  return (
    <Modal opened={opened} onClose={onClose} title="New Case" size="md">
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="e.g. AUR_v2.5_EXT"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            rows={2}
            {...form.getInputProps("description")}
          />
          <Select
            label="Template"
            placeholder="Select template"
            required
            data={templates.map((t) => ({
              value: t.id,
              label: `${t.name} (${t.sim_type})`,
            }))}
            {...form.getInputProps("template_id")}
          />
          <Select
            label="Assembly"
            placeholder="Select assembly"
            required
            data={assemblies.map((a) => ({
              value: a.id,
              label: a.name,
            }))}
            {...form.getInputProps("assembly_id")}
          />
          <Select
            label="Condition Map (optional)"
            placeholder="Assign a map later if needed"
            clearable
            data={maps.map((m) => ({
              value: m.id,
              label: `${m.name} (${m.condition_count} conditions)`,
            }))}
            {...form.getInputProps("map_id")}
          />
          {form.values.map_id && (
            <Switch
              label="Auto-create Runs for all Conditions"
              description="Creates one pending Run per Condition in the selected map"
              {...form.getInputProps("withRuns", { type: "checkbox" })}
            />
          )}
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
