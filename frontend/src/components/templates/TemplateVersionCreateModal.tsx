import { useEffect, useState } from "react";
import {
  Modal,
  TextInput,
  Button,
  Group,
  Badge,
  Text,
  ScrollArea,
  Alert,
  FileButton,
} from "@mantine/core";
import { IconUpload, IconAlertCircle } from "@tabler/icons-react";
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
  const [jsonLoadError, setJsonLoadError] = useState<string | null>(null);
  const [jsonLoading, setJsonLoading] = useState(false);

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

  function handleLoadFromJson(file: File | null) {
    if (!file) return;
    setJsonLoadError(null);
    setJsonLoading(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(text);
      } catch (err) {
        setJsonLoadError(`Invalid JSON syntax: ${String(err)}`);
        setJsonLoading(false);
        return;
      }
      try {
        const result = await templatesApi.validateSettings(parsed);
        if (result.valid && result.normalized) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          form.setValues(valuesFromSettings(result.normalized as any));
          notifications.show({ message: `Form populated from ${file.name}`, color: "green" });
        } else {
          const errCount = result.errors.length;
          setJsonLoadError(
            `Settings invalid (${errCount} error${errCount !== 1 ? "s" : ""}): ` +
              result.errors.slice(0, 3).map((e) => `${e.field}: ${e.message}`).join("; ") +
              (errCount > 3 ? " …" : "")
          );
        }
      } catch (err) {
        setJsonLoadError(`Validation request failed: ${String(err)}`);
      } finally {
        setJsonLoading(false);
      }
    };
    reader.readAsText(file);
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
          <FileButton onChange={handleLoadFromJson} accept="application/json,.json">
            {(props) => (
              <Button
                {...props}
                variant="outline"
                leftSection={<IconUpload size={14} />}
                loading={jsonLoading}
              >
                Load from JSON
              </Button>
            )}
          </FileButton>
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Create Version
          </Button>
        </Group>
        {jsonLoadError && (
          <Alert color="red" icon={<IconAlertCircle size={14} />} mt="xs">
            {jsonLoadError}
          </Alert>
        )}
      </form>
    </Modal>
  );
}
