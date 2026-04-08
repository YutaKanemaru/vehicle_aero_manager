import {
  Modal,
  TextInput,
  Textarea,
  Button,
  Group,
  Stack,
  Text,
  Select,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useRef, useState } from "react";
import { geometriesApi, foldersApi } from "../../api/geometries";
import { useJobsStore } from "../../stores/jobs";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function GeometryUploadModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);
  const updateUploadProgress = useJobsStore((s) => s.updateUploadProgress);
  const removeJob = useJobsStore((s) => s.removeJob);

  const [uploading, setUploading] = useState(false);

  const { data: folders = [] } = useQuery({
    queryKey: ["geometry-folders"],
    queryFn: foldersApi.list,
    enabled: opened,
  });

  const folderOptions = [
    { value: "", label: "— No folder —" },
    ...folders.map((f) => ({ value: f.id, label: f.name })),
  ];

  const form = useForm({
    initialValues: { name: "", description: "", folderId: "" },
    validate: {
      name: (v) => (v.trim() ? null : "Name is required"),
    },
  });

  async function handleSubmit(values: typeof form.values) {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      notifications.show({ message: "Please select an STL file", color: "red" });
      return;
    }

    const tempId = `tmp-${Date.now()}`;
    const name = values.name.trim();
    const folderId = values.folderId || null;

    addJob(tempId, name, "stl_analysis");
    setUploading(true);

    try {
      const data = await geometriesApi.upload(
        name,
        values.description || null,
        folderId,
        file,
        (pct) => updateUploadProgress(tempId, pct),
      );

      // Transition: remove temp job, add real job in pending state
      removeJob(tempId);
      addJob(data.id, data.name, "stl_analysis");
      updateJob(data.id, "pending");

      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      notifications.show({ message: "Upload complete — analysis running in background", color: "green" });
      form.reset();
      if (fileRef.current) fileRef.current.value = "";
      onClose();
    } catch (e) {
      updateJob(tempId, "error", (e as Error).message);
      notifications.show({ message: (e as Error).message, color: "red" });
    } finally {
      setUploading(false);
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Upload STL Geometry" size="md">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="e.g. AUR_v1.2_EXT_1.99"
            required
            disabled={uploading}
            {...form.getInputProps("name")}
          />
          <Textarea
            label="Description"
            placeholder="Optional description"
            disabled={uploading}
            {...form.getInputProps("description")}
          />
          <Select
            label="Folder"
            placeholder="— No folder —"
            data={folderOptions}
            clearable
            disabled={uploading}
            {...form.getInputProps("folderId")}
          />
          <Stack gap={4}>
            <Text size="sm" fw={500}>STL file <Text component="span" c="red">*</Text></Text>
            <input ref={fileRef} type="file" accept=".stl" style={{ fontSize: 14 }} disabled={uploading} />
            <Text size="xs" c="dimmed">Multi-solid ASCII STL supported</Text>
          </Stack>
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={onClose} disabled={uploading}>Cancel</Button>
            <Button type="submit" loading={uploading} disabled={uploading}>
              {uploading ? "Uploading…" : "Upload"}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
