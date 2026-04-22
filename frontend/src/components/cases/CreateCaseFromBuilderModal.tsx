/**
 * CreateCaseFromBuilderModal
 *
 * Opened from the Template Builder page when both an Assembly and a Template are selected.
 * Lets the engineer:
 *   1. Name the Case
 *   2. Pick a Condition Map
 *   3. Preview the conditions that will create Runs
 *   4. For conditions with ride_height.enabled = true, a transform is triggered
 *      automatically using the Template's ride_height config, and the resulting
 *      geometry_override_id is patched onto the Run.
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
  Alert,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { assembliesApi, type GeometryResponse } from "../../api/geometries";
import { templatesApi } from "../../api/templates";
import { transformApi } from "../../api/systems";
import { useJobsStore } from "../../stores/jobs";

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
  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);

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

  // Assembly geometries (for ride-height transform source — use first ready one)
  const geometries: GeometryResponse[] = assembly?.geometries ?? [];
  const firstReadyGeometry = geometries.find((g) => g.status === "ready") ?? null;

  // Template settings (for ride_height template config)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [templateSettings, setTemplateSettings] = useState<any>(null);
  useEffect(() => {
    if (!templateId || !opened) return;
    templatesApi.listVersions(templateId).then((versions) => {
      const active = versions.find((v: { is_active: boolean }) => v.is_active);
      if (active?.settings) setTemplateSettings(active.settings);
    }).catch(() => {});
  }, [templateId, opened]);

  const rhTemplate = templateSettings?.setup_option?.ride_height ?? {
    reference_parts: [],
    adjust_body_wheel_separately: false,
    use_original_wheel_position: false,
  };

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
        const runs = await Promise.all(
          conditions.map((cond) =>
            runsApi.create(newCase.id, {
              name: cond.name,
              condition_id: cond.id,
            })
          )
        );

        // 3. For conditions with ride_height.enabled=true, trigger transform
        //    and patch geometry_override_id onto the Run (fire-and-forget)
        const rhConditions = conditions.filter((c) => c.ride_height?.enabled);
        if (rhConditions.length > 0 && firstReadyGeometry) {
          for (const cond of rhConditions) {
            const run = runs[conditions.indexOf(cond)];
            // Start transform job (background)
            transformApi.transform(firstReadyGeometry.id, {
              name: `${firstReadyGeometry.name}_${cond.name}`,
              condition_id: cond.id,
              ride_height: cond.ride_height ?? { enabled: false },
              rh_template: rhTemplate,
              yaw_angle_deg: cond.yaw_angle,
              yaw_config: cond.yaw_config ?? { center_mode: "wheel_center", center_x: 0, center_y: 0 },
            }).then((result) => {
              // Track in Jobs Drawer
              addJob(result.geometry_id, result.geometry_name, "stl_analysis");
              updateJob(result.geometry_id, "analyzing");
              // Patch geometry_override_id onto the Run once we have the ID
              // Poll until the geometry is ready, then patch
              // For now: patch immediately with the geometry_id (may still be pending)
              runsApi.update(newCase.id, run.id, {
                geometry_override_id: result.geometry_id,
              }).catch((err) => console.warn("patch geometry_override_id failed:", err));
            }).catch((err) => {
              console.warn(`Ride height transform failed for condition ${cond.name}:`, err);
              notifications.show({
                message: `Ride height transform failed for condition "${cond.name}": ${err.message}`,
                color: "orange",
              });
            });
          }
        }
      }

      // 4. Invalidate queries + navigate to /cases
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      notifications.show({
        message: `Case "${newCase.name}" created with ${conditions.length} run(s)`,
        color: "green",
      });
      onClose();
      navigate("/cases");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({ message: `Failed to create case: ${msg}`, color: "red" });
    } finally {
      setIsSubmitting(false);
    }
  }

  const rhEnabledCount = conditions.filter((c) => c.ride_height?.enabled).length;

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
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              )}

              {rhEnabledCount > 0 && (
                <Alert color={firstReadyGeometry ? "teal" : "orange"} radius="sm">
                  {firstReadyGeometry ? (
                    <Text size="xs">
                      {rhEnabledCount} ride-height condition(s) will auto-transform geometry
                      <Text span fw={600}> "{firstReadyGeometry.name}"</Text>.
                      Transforms run in the background (visible in Jobs Drawer).
                    </Text>
                  ) : (
                    <Text size="xs">
                      {rhEnabledCount} ride-height condition(s) require a ready geometry in the
                      assembly, but none is ready yet. Ride-height transforms will be skipped.
                    </Text>
                  )}
                </Alert>
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
