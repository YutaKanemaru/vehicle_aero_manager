"""Write new TemplateCreateModal.tsx and TemplateVersionCreateModal.tsx."""
import pathlib

ROOT = pathlib.Path(r"c:\Users\z0054ymk\OneDrive - Altair Engineering, Inc\PROJECT\C06-DEV\vehicle_aero_manager\frontend\src\components\templates")

CREATE_MODAL = r'''import { useState } from "react";
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
    compute_rotate_wheels: true,
    compute_turbulence_generator: true,
  },
  ghn: {
    coarsest_voxel_size: 0.256,
    number_of_resolution: 9,
    triangle_splitting: false,
    tg_enable_ground: false,
    tg_enable_body: false,
    compute_rotate_wheels: false,
    compute_turbulence_generator: false,
  },
  fan_noise: {
    coarsest_voxel_size: 0.192,
    number_of_resolution: 7,
    triangle_splitting: true,
    tg_enable_ground: false,
    tg_enable_body: false,
    compute_rotate_wheels: false,
    compute_turbulence_generator: false,
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
    <Modal opened={opened} onClose={handleClose} title="New Template" size="xl">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <ScrollArea h="calc(100vh - 160px)" pr="md">
          <Stack>
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
            <TemplateSettingsForm form={form} simType={simType} />
          </Stack>
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
'''

VERSION_MODAL = r'''import { useEffect } from "react";
import {
  Modal,
  TextInput,
  Button,
  Group,
  Stack,
  Badge,
  Text,
  ScrollArea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import {
  templatesApi,
  type TemplateResponse,
  type TemplateVersionCreate,
} from "../../api/templates";
import {
  FORM_DEFAULTS,
  valuesFromSettings,
  buildSettings,
} from "../../hooks/useTemplateSettingsForm";
import { TemplateSettingsForm } from "./TemplateSettingsForm";

interface Props {
  opened: boolean;
  onClose: () => void;
  template: TemplateResponse;
}

export function TemplateVersionCreateModal({ opened, onClose, template }: Props) {
  const queryClient = useQueryClient();
  const simType = template.sim_type as "aero" | "ghn" | "fan_noise";

  const activeSettings = template.active_version?.settings;
  const form = useForm({
    initialValues: activeSettings
      ? valuesFromSettings(activeSettings)
      : { ...FORM_DEFAULTS },
  });

  // Re-populate when template changes or modal re-opens
  useEffect(() => {
    if (opened) {
      form.setValues(
        activeSettings
          ? valuesFromSettings(activeSettings)
          : { ...FORM_DEFAULTS }
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, template]);

  const mutation = useMutation({
    mutationFn: (data: TemplateVersionCreate) =>
      templatesApi.createVersion(template.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      queryClient.invalidateQueries({
        queryKey: ["templates", template.id, "versions"],
      });
      notifications.show({ message: "New version created", color: "green" });
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSubmit(values: typeof form.values) {
    mutation.mutate({
      comment: undefined,
      settings: buildSettings(values, activeSettings),
    });
  }

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="xs">
          <Text fw={600}>New Version</Text>
          <Badge variant="light">{template.name}</Badge>
          <Badge variant="outline" color="gray">
            {simType === "aero"
              ? "External Aero"
              : simType === "ghn"
              ? "GHN"
              : "Fan Noise"}
          </Badge>
        </Group>
      }
      size="xl"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <ScrollArea h="calc(100vh - 160px)" pr="md">
          <Stack>
            <TextInput label="Version comment" placeholder="Optional comment" />
            <TemplateSettingsForm form={form} simType={simType} />
          </Stack>
        </ScrollArea>
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Create Version
          </Button>
        </Group>
      </form>
    </Modal>
  );
}
'''

(ROOT / "TemplateCreateModal.tsx").write_text(CREATE_MODAL, encoding="utf-8")
(ROOT / "TemplateVersionCreateModal.tsx").write_text(VERSION_MODAL, encoding="utf-8")
print("Done")
