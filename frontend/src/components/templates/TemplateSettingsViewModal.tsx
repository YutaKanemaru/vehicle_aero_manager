import { useEffect } from "react";
import {
  Modal,
  Group,
  Text,
  Badge,
  TextInput,
  Textarea,
  Select,
  Stack,
  ScrollArea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import type { TemplateVersionResponse } from "../../api/templates";
import {
  FORM_DEFAULTS,
  valuesFromSettings,
} from "../../hooks/useTemplateSettingsForm";
import { TemplateSettingsForm } from "./TemplateSettingsForm";

interface Props {
  opened: boolean;
  onClose: () => void;
  version: TemplateVersionResponse;
  templateName: string;
  simType: string;
  description?: string;
}

export function TemplateSettingsViewModal({
  opened,
  onClose,
  version,
  templateName,
  simType,
  description,
}: Props) {
  const form = useForm({
    initialValues: version.settings
      ? valuesFromSettings(version.settings)
      : { ...FORM_DEFAULTS },
  });

  useEffect(() => {
    if (opened) {
      form.setValues(
        version.settings
          ? valuesFromSettings(version.settings)
          : { ...FORM_DEFAULTS }
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, version]);

  const simTypeLabel =
    simType === "aero"
      ? "External Aerodynamics"
      : simType === "ghn"
      ? "Greenhouse Noise (GHN)"
      : "Fan Noise";

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="sm">
          <Text fw={600}>{templateName}</Text>
          <Badge variant="light" color={simType === "aero" ? "blue" : "violet"}>
            {simType.toUpperCase()}
          </Badge>
          <Badge variant="outline" color="gray" size="sm">
            v{version.version_number}
            {version.is_active ? " · Active" : ""}
          </Badge>
        </Group>
      }
      size="90%"
    >
        <ScrollArea h="calc(100vh - 160px)" pr="md">
          <TemplateSettingsForm
            form={form}
            simType={simType}
            readOnly
            generalContent={
              <Stack gap="sm">
                <TextInput label="Name" value={templateName} readOnly />
                {description && (
                  <Textarea label="Description" value={description} readOnly />
                )}
                <Select
                  label="Application"
                  value={simType}
                  data={[
                    { value: "aero", label: "External Aerodynamics" },
                    { value: "ghn", label: "Greenhouse Noise (GHN)" },
                    { value: "fan_noise", label: "Fan Noise" },
                  ]}
                  readOnly
                />
                <TextInput
                  label="Version comment"
                  value={version.comment ?? ""}
                  readOnly
                />
                <Text size="xs" c="dimmed">
                  Application: <strong>{simTypeLabel}</strong> · Read-only view
                </Text>
              </Stack>
            }
          />
        </ScrollArea>
    </Modal>
  );
}
