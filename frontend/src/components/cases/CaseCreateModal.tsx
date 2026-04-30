import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Button,
  Stack,
  Group,
  Tabs,
  Badge,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { casesApi, mapsApi, type CaseCreate, type CaseDuplicateRequest } from "../../api/configurations";
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

  const { data: allCases = [] } = useQuery({
    queryKey: ["cases"],
    queryFn: casesApi.list,
  });

  // ── New Case form ────────────────────────────────────────────────────────
  const form = useForm<CaseCreate>({
    initialValues: {
      name: "",
      description: "",
      template_id: "",
      assembly_id: "",
      map_id: null,
    },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
      template_id: (v) => (v ? null : "Template is required"),
      assembly_id: (v) => (v ? null : "Assembly is required"),
      map_id: (v) => (v ? null : "Condition Map is required"),
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: CaseCreate) => {
      return casesApi.create(data, true);
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

  // ── Copy from Case form ──────────────────────────────────────────────────
  const copyForm = useForm<{ sourceId: string; name: string; description: string }>({
    initialValues: { sourceId: "", name: "", description: "" },
    validate: {
      sourceId: (v) => (v ? null : "Source case is required"),
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const selectedSource = allCases.find((c) => c.id === copyForm.values.sourceId) ?? null;

  const copyMutation = useMutation({
    mutationFn: (data: { sourceId: string } & CaseDuplicateRequest) => {
      const { sourceId, ...req } = data;
      return casesApi.duplicate(sourceId, req);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({ message: "Case copied", color: "green" });
      copyForm.reset();
      onClose();
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  function handleSourceChange(id: string | null) {
    const src = allCases.find((c) => c.id === id) ?? null;
    copyForm.setValues({
      sourceId: id ?? "",
      name: src ? `Copy of ${src.name}` : "",
      description: src?.description ?? "",
    });
  }

  const handleClose = () => {
    form.reset();
    copyForm.reset();
    onClose();
  };

  return (
    <Modal opened={opened} onClose={handleClose} title="New Case" size="md">
      <Tabs defaultValue="new">
        <Tabs.List mb="md">
          <Tabs.Tab value="new">New Case</Tabs.Tab>
          <Tabs.Tab value="copy">Copy from Case</Tabs.Tab>
        </Tabs.List>

        {/* ── New Case tab ─────────────────────────────────────────────── */}
        <Tabs.Panel value="new">
          <form onSubmit={form.onSubmit((v) => createMutation.mutate(v))}>
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
                label="Condition Map"
                placeholder="Select a condition map"
                required
                data={maps.map((m) => ({
                  value: m.id,
                  label: `${m.name} (${m.condition_count} conditions)`,
                }))}
                {...form.getInputProps("map_id")}
              />
              <Group justify="flex-end" mt="sm">
                <Button variant="subtle" onClick={handleClose}>Cancel</Button>
                <Button type="submit" loading={createMutation.isPending}>Create</Button>
              </Group>
            </Stack>
          </form>
        </Tabs.Panel>

        {/* ── Copy from Case tab ───────────────────────────────────────── */}
        <Tabs.Panel value="copy">
          <form
            onSubmit={copyForm.onSubmit((v) =>
              copyMutation.mutate({ sourceId: v.sourceId, name: v.name, description: v.description })
            )}
          >
            <Stack>
              <Select
                label="Source Case"
                placeholder="Select case to copy..."
                searchable
                data={allCases.map((c) => ({
                  value: c.id,
                  label: `${c.case_number ? `[${c.case_number}] ` : ""}${c.name}`,
                }))}
                value={copyForm.values.sourceId || null}
                onChange={handleSourceChange}
                error={copyForm.errors.sourceId}
              />
              {selectedSource && (
                <Group gap="xs">
                  <Badge variant="light" color="violet" size="sm">
                    {selectedSource.template_name || selectedSource.template_id.slice(0, 8)}
                  </Badge>
                  <Badge variant="light" color="teal" size="sm">
                    {selectedSource.assembly_name || selectedSource.assembly_id.slice(0, 8)}
                  </Badge>
                  <Text size="xs" c="dimmed">{selectedSource.run_count ?? 0} runs</Text>
                </Group>
              )}
              <TextInput
                label="New Name"
                placeholder="Name for the copy"
                required
                {...copyForm.getInputProps("name")}
              />
              <Textarea
                label="Description"
                placeholder="Optional"
                rows={2}
                {...copyForm.getInputProps("description")}
              />
              <Group justify="flex-end" mt="sm">
                <Button variant="subtle" onClick={handleClose}>Cancel</Button>
                <Button type="submit" loading={copyMutation.isPending}>Copy</Button>
              </Group>
            </Stack>
          </form>
        </Tabs.Panel>
      </Tabs>
    </Modal>
  );
}
