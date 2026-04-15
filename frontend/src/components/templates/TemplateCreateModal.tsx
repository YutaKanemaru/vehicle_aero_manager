import { useState, useEffect, useRef } from "react";
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
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type TemplateCreate } from "../../api/templates";
import {
  FORM_DEFAULTS,
  buildSettings,
  valuesFromSettings,
} from "../../hooks/useTemplateSettingsForm";
import { TemplateSettingsForm } from "./TemplateSettingsForm";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function TemplateCreateModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const [simType, setSimType] = useState<"aero" | "ghn" | "fan_noise">("aero");
  const [pendingPresetApply, setPendingPresetApply] = useState(false);
  const [nameValue, setNameValue] = useState("");
  const [descValue, setDescValue] = useState("");
  const [commentValue, setCommentValue] = useState("");
  const closeAfterSave = useRef(false);

  const form = useForm({ initialValues: { ...FORM_DEFAULTS } });

  // Fetch preset from backend whenever sim_type changes
  const { data: presetData } = useQuery({
    queryKey: ["template-preset", simType],
    queryFn: () => templatesApi.getPreset(simType),
    staleTime: Infinity, // presets are static — never refetch
  });

  // Apply the preset to the form only when the user explicitly changes sim_type
  useEffect(() => {
    if (pendingPresetApply && presetData) {
      form.setValues(valuesFromSettings(presetData));
      setPendingPresetApply(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingPresetApply, presetData]);

  const mutation = useMutation({
    mutationFn: (data: TemplateCreate) => templatesApi.create(data),
    onSuccess: () => {
      const shouldClose = closeAfterSave.current;
      closeAfterSave.current = false;
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template created", color: "green" });
      form.reset();
      setSimType("aero");
      setPendingPresetApply(false);
      setNameValue("");
      setDescValue("");
      setCommentValue("");
      if (shouldClose) onClose();
    },
    onError: (e: Error) => {
      closeAfterSave.current = false;
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleSimTypeChange(value: string | null) {
    const t = (value ?? "aero") as "aero" | "ghn" | "fan_noise";
    setSimType(t);
    setPendingPresetApply(true);
  }

  function handleSubmit(values: typeof form.values) {
    if (!nameValue.trim()) {
      closeAfterSave.current = false;
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
    setPendingPresetApply(false);
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
            Save without closing
          </Button>
          <Button
            type="button"
            variant="outline"
            loading={mutation.isPending}
            onClick={() => {
              closeAfterSave.current = true;
              form.onSubmit(handleSubmit)();
            }}
          >
            Save and close
          </Button>
        </Group>
      </form>
    </Modal>
  );
}
