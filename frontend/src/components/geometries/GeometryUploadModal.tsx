import {
  Modal,
  TextInput,
  Textarea,
  Button,
  Group,
  Stack,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useRef } from "react";
import { geometriesApi, type GeometryResponse } from "../../api/geometries";
import { useJobsStore } from "../../stores/jobs";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function GeometryUploadModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const addJob = useJobsStore((s) => s.addJob);

  const form = useForm({
    initialValues: { name: "", description: "" },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  const mutation = useMutation({
    mutationFn: ({ name, description, file }: { name: string; description: string; file: File }) =>
      geometriesApi.upload(name, description || null, file),
    onSuccess: (data: GeometryResponse) => {
      addJob(data.id, data.name, "stl_analysis");
      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      notifications.show({ message: "Upload started — analysis running in background", color: "green" });
      form.reset();
      if (fileRef.current) fileRef.current.value = "";
      onClose();
    },
    onError: (e: Error) => notifications.show({ message: e.message, color: "red" }),
  });

  function handleSubmit(values: typeof form.values) {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      notifications.show({ message: "Please select an STL file", color: "red" });
      return;
    }
    mutation.mutate({ name: values.name.trim(), description: values.description, file });
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Upload STL Geometry" size="md">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="e.g. AUR_v1.2_EXT_1.99"
            required
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            {...form.getInputProps("description")}
          />
          <Stack gap={4}>
            <Text size="sm" fw={500}>STL file <Text component="span" c="red">*</Text></Text>
            <input ref={fileRef} type="file" accept=".stl" style={{ fontSize: 14 }} />
            <Text size="xs" c="dimmed">Multi-solid ASCII STL supported</Text>
          </Stack>
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={mutation.isPending}>Upload</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
