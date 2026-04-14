import { useEffect, useState } from "react";
import {
  Modal,
  TextInput,
  Button,
  Group,
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
  const [commentValue, setCommentValue] = useState("");

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
      setCommentValue("");
      onClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSubmit(values: typeof form.values) {
    mutation.mutate({
      comment: commentValue.trim() || undefined,
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
      size="90%"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <ScrollArea h="calc(100vh - 160px)" pr="md">
          <TemplateSettingsForm
            form={form}
            simType={simType}
            generalContent={
              <TextInput
                label="Version comment"
                placeholder="Optional comment"
                value={commentValue}
                onChange={(e) => setCommentValue(e.currentTarget.value)}
              />
            }
          />
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
