import { useState } from "react";
import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Button,
  Group,
  Stack,
  Text,
  ScrollArea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateCreate } from "../../api/templates";
import {
  FORM_DEFAULTS,
  buildSettings,
} from "../../hooks/useTemplateSettingsForm";
import { TemplateSettingsForm } from "./TemplateSettingsForm";

interface Props {
  opened: boolean;
  onClose: () => void;
}

// Preset defaults per sim_type
const SIM_TYPE_PRESETS: Record<string, Partial<typeof FORM_DEFAULTS>> = {
  aero: {
    coarsest_voxel_size: 0.192,
    number_of_resolution: 7,
    triangle_splitting: true,
    tg_enable_ground: true,
    tg_enable_body: true,
  },
  ghn: {
    coarsest_voxel_size: 0.256,
    number_of_resolution: 9,
    triangle_splitting: false,
    tg_enable_ground: false,
    tg_enable_body: false,
  },
  fan_noise: {
    coarsest_voxel_size: 0.192,
    number_of_resolution: 7,
    triangle_splitting: true,
    tg_enable_ground: false,
    tg_enable_body: false,
  },
};

export function TemplateCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const [simType, setSimType] = useState<"aero" | "ghn" | "fan_noise">("aero");
  const [nameValue, setNameValue] = useState("");
  const [descValue, setDescValue] = useState("");
  const [commentValue, setCommentValue] = useState("");

  const form = useForm({ initialValues: { ...FORM_DEFAULTS } });

  const mutation = useMutation({
    mutationFn: (data: TemplateCreate) => templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template created", color: "green" });
      form.reset();
      setSimType("aero");
      setNameValue("");
      setDescValue("");
      setCommentValue("");
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSimTypeChange(value: string | null) {
    const t = (value ?? "aero") as "aero" | "ghn" | "fan_noise";
    setSimType(t);
    const preset = SIM_TYPE_PRESETS[t] ?? {};
    form.setValues({ ...form.values, ...preset });
  }

  function handleSubmit(values: typeof form.values) {
    if (!nameValue.trim()) {
      notifications.show({ message: "Name is required", color: "red" });
      return;
    }
    mutation.mutate({
      name: nameValue.trim(),
      description: descValue.trim() || undefined,
      sim_type: simType,
      comment: commentValue.trim() || undefined,
      settings: buildSettings(values),
    });
  }

  function handleClose() {
    form.reset();
    setSimType("aero");
    setNameValue("");
    setDescValue("");
    setCommentValue("");
    onClose();
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="New Template" size="90%">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <ScrollArea h="calc(100vh - 160px)" pr="md">
          <TemplateSettingsForm
            form={form}
            simType={simType}
            generalContent={
              <Stack gap="sm">
                <TextInput
                  label="Name"
                  placeholder="e.g. Aero_Standard_2026"
                  required
                  value={nameValue}
                  onChange={(e) => setNameValue(e.currentTarget.value)}
                />
                <Textarea
                  label="Description"
                  placeholder="Optional description"
                  value={descValue}
                  onChange={(e) => setDescValue(e.currentTarget.value)}
                />
                <Select
                  label="Application"
                  data={[
                    { value: "aero", label: "External Aerodynamics" },
                    { value: "ghn", label: "Greenhouse Noise (GHN)" },
                    { value: "fan_noise", label: "Fan Noise" },
                  ]}
                  value={simType}
                  onChange={handleSimTypeChange}
                />
                <TextInput
                  label="Version comment"
                  placeholder="Initial version"
                  value={commentValue}
                  onChange={(e) => setCommentValue(e.currentTarget.value)}
                />
                <Text size="sm" c="dimmed">
                  Preset defaults applied for{" "}
                  <strong>
                    {simType === "aero"
                      ? "External Aerodynamics"
                      : simType === "ghn"
                      ? "GHN"
                      : "Fan Noise"}
                  </strong>
                  . Adjust as needed.
                </Text>
              </Stack>
            }
          />
        </ScrollArea>
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Create Template
          </Button>
        </Group>
      </form>
    </Modal>
  );
}
