/**
 * CreateCaseFromBuilderModal
 *
 * Opened from the Template Builder page when both an Assembly and a Template are selected.
 * Lets the engineer:
 *   1. Name the Case
 *   2. Pick a Condition Map
 *   3. Preview the conditions that will create Runs
 *
 * Transforms (ride height / yaw) are NOT triggered here — they are applied
 * per-Run on the CaseDetailPage via "Apply Transform" buttons.
 */
import { useEffect, useState } from "react";
import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Button,
  Stack,
  Text,
  Badge,
  Group,
  Table,
  Divider,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useNavigate } from "react-router-dom";
import {
  casesApi,
  mapsApi,
  conditionsApi,
  runsApi,
  type ConditionResponse,
  type CaseResponse,
} from "../../api/configurations";
import { assembliesApi } from "../../api/geometries";
import { templatesApi } from "../../api/templates";

// ── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  opened: boolean;
  onClose: () => void;
  assemblyId: string;
  templateId: string;
}

// ── Form values ───────────────────────────────────────────────────────────────

interface FormValues {
  name: string;
  description: string;
  mapId: string | null;
}

// ── Helper: default case name ─────────────────────────────────────────────────

function buildDefaultName(
  assemblyName: string | undefined,
  templateName: string | undefined,
  mapName: string | undefined,
): string {
  const parts = [assemblyName, templateName, mapName].filter(Boolean);
  return parts.join("_");
}

// ── Component ─────────────────────────────────────────────────────────────────

export function CreateCaseFromBuilderModal({
  opened,
  onClose,
  assemblyId,
  templateId,
}: Props) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch context data
  const { data: assembly } = useQuery({
    queryKey: ["assembly", assemblyId],
    queryFn: () => assembliesApi.get(assemblyId),
    enabled: opened && !!assemblyId,
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: () => templatesApi.list(),
    enabled: opened,
  });
  const { data: maps = [] } = useQuery({
    queryKey: ["maps"],
    queryFn: mapsApi.list,
    enabled: opened,
  });

  const template = templates.find((t) => t.id === templateId);

  const form = useForm<FormValues>({
    initialValues: {
      name: "",
      description: "",
      mapId: null,
    },
    validate: {
      name: (v) => (v.trim() ? null : "Case name is required"),
    },
  });

  // Update default name when assembly / template / map changes
  const mapName = maps.find((m) => m.id === form.values.mapId)?.name;
  useEffect(() => {
    if (!opened) return;
    form.setFieldValue("name", buildDefaultName(assembly?.name, template?.name, mapName));
  }, [assembly?.name, template?.name, mapName, opened]); // eslint-disable-line react-hooks/exhaustive-deps

  // Conditions for selected map
  const { data: conditions = [] } = useQuery<ConditionResponse[]>({
    queryKey: ["conditions", form.values.mapId],
    queryFn: () => conditionsApi.list(form.values.mapId!),
    enabled: !!form.values.mapId,
  });

  // ── Submission ───────────────────────────────────────────────────────────────

  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      // 1. Create the Case
      const newCase: CaseResponse = await casesApi.create({
        name: values.name.trim(),
        description: values.description.trim() || undefined,
        template_id: templateId,
        assembly_id: assemblyId,
        map_id: values.mapId || undefined,
      });

      // 2. Create a Run for each Condition (parallel)
      if (conditions.length > 0) {
        await Promise.all(
          conditions.map((cond) =>
            runsApi.create(newCase.id, {
              name: cond.name,
              condition_id: cond.id,
              comment: "",
            })
          )
        );
      }

      // 3. Invalidate queries + navigate to /cases/:id
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({
        message: `Case "${newCase.name}" created with ${conditions.length} run(s)`,
        color: "green",
      });
      onClose();
      navigate(`/cases/${newCase.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({ message: `Failed to create case: ${msg}`, color: "red" });
    } finally {
      setIsSubmitting(false);
    }
  }

  const transformCount = conditions.filter(
    (c) => c.ride_height?.enabled || (c.yaw_angle !== 0 && c.yaw_angle !== undefined)
  ).length;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Create Case from Template Builder"
      size="md"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="sm">
          <TextInput
            label="Case Name"
            placeholder="Assembly_Template_Map"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            rows={2}
            {...form.getInputProps("description")}
          />

          <Divider label="Condition Map" labelPosition="left" />

          <Select
            label="Condition Map"
            placeholder="— No map (empty case) —"
            data={maps.map((m) => ({ value: m.id, label: m.name }))}
            value={form.values.mapId}
            onChange={(v) => form.setFieldValue("mapId", v)}
            clearable
          />

          {form.values.mapId && (
            <>
              <Text size="xs" c="dimmed">
                {conditions.length} condition(s) → {conditions.length} run(s) will be created
              </Text>
              {conditions.length > 0 && (
                <Table fz="xs" withTableBorder withRowBorders={false}>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Condition</Table.Th>
                      <Table.Th>Velocity</Table.Th>
                      <Table.Th>Yaw</Table.Th>
                      <Table.Th>RH</Table.Th>
                      <Table.Th>Transform</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {conditions.map((c) => (
                      <Table.Tr key={c.id}>
                        <Table.Td>{c.name}</Table.Td>
                        <Table.Td>{c.inflow_velocity} m/s</Table.Td>
                        <Table.Td>{c.yaw_angle}°</Table.Td>
                        <Table.Td>
                          {c.ride_height?.enabled ? (
                            <Badge size="xs" color="teal">On</Badge>
                          ) : (
                            <Text size="xs" c="dimmed">—</Text>
                          )}
                        </Table.Td>
                        <Table.Td>
                          {(c.ride_height?.enabled || (c.yaw_angle !== 0 && c.yaw_angle !== undefined)) ? (
                            <Badge size="xs" color="orange">Required</Badge>
                          ) : (
                            <Text size="xs" c="dimmed">—</Text>
                          )}
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              )}

              {transformCount > 0 && (
                <Text size="xs" c="orange" fw={500}>
                  {transformCount} run(s) require geometry transform (ride height / yaw).
                  Apply transforms on the Case detail page before generating XML.
                </Text>
              )}
            </>
          )}

          <Group justify="flex-end" mt="sm">
            <Button variant="default" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              Create Case
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
