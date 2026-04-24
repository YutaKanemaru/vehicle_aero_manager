import {
  Modal,
  TextInput,
  NumberInput,
  Switch,
  Select,
  Button,
  Stack,
  Group,
  Accordion,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import {
  conditionsApi,
  type ConditionCreate,
  type ConditionResponse,
} from "../../api/configurations";

// ── Form value types ──────────────────────────────────────────────────────────

interface FormValues {
  name: string;
  inflow_velocity: number;
  yaw_angle: number;
  // ride height
  rh_enabled: boolean;
  rh_target_front: number | "";
  rh_target_rear: number | "";
  rh_wheel_front: number | "";
  rh_wheel_rear: number | "";
  // yaw config
  yaw_center_mode: "wheel_center" | "user_input";
  yaw_center_x: number;
  yaw_center_y: number;
}

function defaultValues(cond?: ConditionResponse): FormValues {
  const rh = cond?.ride_height;
  const yc = cond?.yaw_config;
  return {
    name: cond?.name ?? "",
    inflow_velocity: cond?.inflow_velocity ?? 38.88,
    yaw_angle: cond?.yaw_angle ?? 0,
    rh_enabled: rh?.enabled ?? false,
    rh_target_front: rh?.target_front_wheel_axis_rh ?? "",
    rh_target_rear: rh?.target_rear_wheel_axis_rh ?? "",
    rh_wheel_front: rh?.target_front_wheel_rh ?? "",
    rh_wheel_rear: rh?.target_rear_wheel_rh ?? "",
    yaw_center_mode: yc?.center_mode ?? "wheel_center",
    yaw_center_x: yc?.center_x ?? 0,
    yaw_center_y: yc?.center_y ?? 0,
  };
}

function toConditionCreate(v: FormValues): ConditionCreate {
  return {
    name: v.name,
    inflow_velocity: v.inflow_velocity,
    yaw_angle: v.yaw_angle,
    ride_height: {
      enabled: v.rh_enabled,
      target_front_wheel_axis_rh: v.rh_enabled && v.rh_target_front !== "" ? Number(v.rh_target_front) : null,
      target_rear_wheel_axis_rh: v.rh_enabled && v.rh_target_rear !== "" ? Number(v.rh_target_rear) : null,
      target_front_wheel_rh: v.rh_enabled && v.rh_wheel_front !== "" ? Number(v.rh_wheel_front) : null,
      target_rear_wheel_rh: v.rh_enabled && v.rh_wheel_rear !== "" ? Number(v.rh_wheel_rear) : null,
    },
    yaw_config: {
      center_mode: v.yaw_center_mode,
      center_x: v.yaw_center_x,
      center_y: v.yaw_center_y,
    },
  };
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  opened: boolean;
  onClose: () => void;
  mapId: string;
  /** When provided — edit mode. When absent — create mode. */
  condition?: ConditionResponse;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ConditionFormModal({ opened, onClose, mapId, condition }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!condition;

  const form = useForm<FormValues>({
    initialValues: defaultValues(condition),
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
      inflow_velocity: (v) => (v > 0 ? null : "Must be > 0"),
    },
  });

  // Reset form when modal opens
  const handleOpen = () => {
    form.setValues(defaultValues(condition));
    form.clearErrors();
  };

  const mutation = useMutation({
    mutationFn: (data: ConditionCreate) =>
      isEdit
        ? conditionsApi.update(mapId, condition!.id, data)
        : conditionsApi.create(mapId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conditions", mapId] });
      queryClient.invalidateQueries({ queryKey: ["maps"] });
      notifications.show({
        message: isEdit ? "Condition updated" : "Condition added",
        color: "green",
      });
      onClose();
    },
    onError: (e: Error) =>
      notifications.show({ message: e.message, color: "red" }),
  });

  const v = form.values;
  const showRhFields = v.rh_enabled;
  const showYawCenter = v.yaw_center_mode === "user_input";

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={isEdit ? `Edit Condition — ${condition!.name}` : "Add Condition"}
      size="md"
      onFocus={() => { if (opened) {} }}
      // re-init each open
      key={condition?.id ?? "new"}
    >
      <form onSubmit={form.onSubmit((vals) => mutation.mutate(toConditionCreate(vals)))}>
        <Stack gap="xs">
          {/* ── Basic ── */}
          <TextInput
            label="Name"
            placeholder="e.g. 140kph_yaw0"
            required
            {...form.getInputProps("name")}
          />
          <Group gap="sm" grow>
            <NumberInput
              label="Inflow Velocity (m/s)"
              required
              min={0.1}
              step={0.01}
              decimalScale={3}
              {...form.getInputProps("inflow_velocity")}
            />
            <NumberInput
              label="Yaw Angle (deg)"
              step={0.5}
              decimalScale={2}
              {...form.getInputProps("yaw_angle")}
            />
          </Group>

          {/* ── Ride Height ── */}
          <Accordion variant="contained" mt="xs">
            <Accordion.Item value="rh">
              <Accordion.Control>
                <Group gap="xs">
                  <Text size="sm" fw={500}>Ride Height Transform</Text>
                  {v.rh_enabled && (
                    <Text size="xs" c="teal">(enabled)</Text>
                  )}
                </Group>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Switch
                    label="Enable ride height adjustment"
                    {...form.getInputProps("rh_enabled", { type: "checkbox" })}
                  />
                  {showRhFields && (
                    <>
                      <Group gap="sm" grow>
                        <NumberInput
                          label="Target front axis height (m)"
                          placeholder="e.g. 0.335"
                          step={0.001}
                          decimalScale={4}
                          min={0}
                          value={v.rh_target_front}
                          onChange={(val) => form.setFieldValue("rh_target_front", val)}
                          error={form.errors["rh_target_front"]}
                        />
                        <NumberInput
                          label="Target rear axis height (m)"
                          placeholder="e.g. 0.335"
                          step={0.001}
                          decimalScale={4}
                          min={0}
                          value={v.rh_target_rear}
                          onChange={(val) => form.setFieldValue("rh_target_rear", val)}
                          error={form.errors["rh_target_rear"]}
                        />
                      </Group>
                      <Group gap="sm" grow>
                        <NumberInput
                          label="Front wheel RH — body-separated (m, optional)"
                          description="Only applied when Template uses adjust-separately mode"
                          placeholder="e.g. 0.335"
                          step={0.001}
                          decimalScale={4}
                          min={0}
                          value={v.rh_wheel_front}
                          onChange={(val) => form.setFieldValue("rh_wheel_front", val)}
                        />
                        <NumberInput
                          label="Rear wheel RH — body-separated (m, optional)"
                          description="Only applied when Template uses adjust-separately mode"
                          placeholder="e.g. 0.335"
                          step={0.001}
                          decimalScale={4}
                          min={0}
                          value={v.rh_wheel_rear}
                          onChange={(val) => form.setFieldValue("rh_wheel_rear", val)}
                        />
                      </Group>
                    </>
                  )}
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* ── Yaw Config ── */}
            <Accordion.Item value="yaw">
              <Accordion.Control>
                <Text size="sm" fw={500}>Yaw Center Configuration</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="xs">
                  <Select
                    label="Yaw center mode"
                    data={[
                      { value: "wheel_center", label: "Wheel-axis midpoint (auto)" },
                      { value: "user_input", label: "User-defined point" },
                    ]}
                    {...form.getInputProps("yaw_center_mode")}
                  />
                  {showYawCenter && (
                    <Group gap="sm" grow>
                      <NumberInput
                        label="Center X (m)"
                        step={0.01}
                        decimalScale={4}
                        {...form.getInputProps("yaw_center_x")}
                      />
                      <NumberInput
                        label="Center Y (m)"
                        step={0.01}
                        decimalScale={4}
                        {...form.getInputProps("yaw_center_y")}
                      />
                    </Group>
                  )}
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>

          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              {isEdit ? "Save Changes" : "Add"}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
