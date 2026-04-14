import { useState } from "react";
import {
  Modal,
  Stack,
  TextInput,
  Select,
  Button,
  Group,
  Alert,
  Text,
  Table,
  FileButton,
  ScrollArea,
  Badge,
  Divider,
} from "@mantine/core";
import { IconUpload, IconAlertCircle, IconCheck } from "@tabler/icons-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { templatesApi, type SettingsValidateResponse } from "../../api/templates";

interface Props {
  opened: boolean;
  onClose: () => void;
}

type ValidationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "syntax_error"; message: string }
  | { status: "valid"; normalized: Record<string, unknown> }
  | { status: "invalid"; errors: SettingsValidateResponse["errors"] };

export function TemplateImportModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [simType, setSimType] = useState<"aero" | "ghn" | "fan_noise">("aero");
  const [comment, setComment] = useState("");
  const [validation, setValidation] = useState<ValidationState>({ status: "idle" });
  const [fileName, setFileName] = useState<string | null>(null);

  const validateMutation = useMutation({
    mutationFn: (settings: Record<string, unknown>) =>
      templatesApi.validateSettings(settings),
    onSuccess: (result) => {
      if (result.valid && result.normalized) {
        setValidation({ status: "valid", normalized: result.normalized as Record<string, unknown> });
      } else {
        setValidation({ status: "invalid", errors: result.errors });
      }
    },
    onError: (e: Error) => {
      setValidation({ status: "idle" });
      notifications.show({ message: `Validation request failed: ${e.message}`, color: "red" });
    },
  });

  const createMutation = useMutation({
    mutationFn: () => {
      if (validation.status !== "valid") throw new Error("Settings not validated");
      return templatesApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        sim_type: simType,
        comment: comment.trim() || undefined,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        settings: validation.normalized as any,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      notifications.show({ message: "Template created from JSON", color: "green" });
      handleClose();
    },
    onError: (e: Error) => {
      notifications.show({ message: e.message, color: "red" });
    },
  });

  function handleFile(file: File | null) {
    if (!file) return;
    setFileName(file.name);
    setValidation({ status: "loading" });
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(text);
      } catch (err) {
        setValidation({ status: "syntax_error", message: String(err) });
        return;
      }
      validateMutation.mutate(parsed);
    };
    reader.readAsText(file);
  }

  function handleClose() {
    setName("");
    setDescription("");
    setSimType("aero");
    setComment("");
    setValidation({ status: "idle" });
    setFileName(null);
    onClose();
  }

  const isValid = validation.status === "valid";
  const isLoading = validation.status === "loading" || validateMutation.isPending;

  return (
    <Modal opened={opened} onClose={handleClose} title="Create Template from JSON" size="lg">
      <Stack gap="sm">
        {/* File selector */}
        <Group>
          <FileButton onChange={handleFile} accept="application/json,.json">
            {(props) => (
              <Button
                {...props}
                variant="outline"
                leftSection={<IconUpload size={16} />}
                loading={isLoading}
              >
                Select JSON file
              </Button>
            )}
          </FileButton>
          {fileName && (
            <Group gap="xs">
              <Text size="sm" c="dimmed">{fileName}</Text>
              {isValid && <Badge color="green" size="sm">Valid</Badge>}
              {validation.status === "invalid" && <Badge color="red" size="sm">Invalid</Badge>}
              {validation.status === "syntax_error" && <Badge color="red" size="sm">Syntax error</Badge>}
            </Group>
          )}
        </Group>

        {/* Syntax error */}
        {validation.status === "syntax_error" && (
          <Alert color="red" icon={<IconAlertCircle size={16} />} title="Invalid JSON syntax">
            <Text size="xs" ff="monospace">{validation.message}</Text>
          </Alert>
        )}

        {/* Validation errors */}
        {validation.status === "invalid" && validation.errors.length > 0 && (
          <Alert
            color="red"
            icon={<IconAlertCircle size={16} />}
            title={`Validation failed — ${validation.errors.length} error(s)`}
          >
            <ScrollArea.Autosize mah={200}>
              <Table fz="xs" withTableBorder mt={6}>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Field</Table.Th>
                    <Table.Th>Error</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {validation.errors.map((err, i) => (
                    <Table.Tr key={i}>
                      <Table.Td>
                        <Text ff="monospace" fz="xs" c="red">{err.field}</Text>
                      </Table.Td>
                      <Table.Td>{err.message}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea.Autosize>
          </Alert>
        )}

        {/* Valid */}
        {isValid && (
          <Alert color="green" icon={<IconCheck size={16} />}>
            Settings are valid. Fill in the template details below.
          </Alert>
        )}

        <Divider />

        {/* Template metadata */}
        <TextInput
          label="Template name"
          placeholder="My Template"
          required
          disabled={!isValid}
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
        />
        <TextInput
          label="Description"
          placeholder="Optional description"
          disabled={!isValid}
          value={description}
          onChange={(e) => setDescription(e.currentTarget.value)}
        />
        <Select
          label="Application"
          data={[
            { value: "aero", label: "Aero" },
            { value: "ghn", label: "GHN" },
            { value: "fan_noise", label: "Fan Noise" },
          ]}
          disabled={!isValid}
          value={simType}
          onChange={(v) => v && setSimType(v as "aero" | "ghn" | "fan_noise")}
        />
        <TextInput
          label="Version comment"
          placeholder="Imported from JSON"
          disabled={!isValid}
          value={comment}
          onChange={(e) => setComment(e.currentTarget.value)}
        />

        <Group justify="flex-end">
          <Button variant="subtle" onClick={handleClose}>Cancel</Button>
          <Button
            disabled={!isValid || !name.trim()}
            loading={createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Create Template
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
