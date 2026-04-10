import {
  Modal,
  Textarea,
  Button,
  Group,
  Stack,
  Text,
  Select,
  Badge,
  List,
  ThemeIcon,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { useRef, useState } from "react";
import { IconFile } from "@tabler/icons-react";
import { geometriesApi, foldersApi } from "../../api/geometries";
import { useJobsStore } from "../../stores/jobs";

interface Props {
  opened: boolean;
  onClose: () => void;
}

function stemName(filename: string): string {
  return filename.replace(/\.[^.]+$/, "");
}

export function GeometryUploadModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);
  const updateUploadProgress = useJobsStore((s) => s.updateUploadProgress);
  const removeJob = useJobsStore((s) => s.removeJob);

  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

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
    initialValues: { description: "", folderId: "" },
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFiles(Array.from(e.target.files ?? []));
  }

  async function handleSubmit(values: typeof form.values) {
    if (selectedFiles.length === 0) {
      notifications.show({ message: "STL ファイルを選択してください", color: "red" });
      return;
    }

    const folderId = values.folderId || null;
    setUploading(true);

    // ファイルごとに一時ジョブを登録してから並列アップロード
    const jobs = selectedFiles.map((file) => {
      const tempId = `tmp-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const name = stemName(file.name);
      addJob(tempId, name, "stl_analysis");
      return { tempId, name, file };
    });

    const results = await Promise.allSettled(
      jobs.map(({ tempId, name, file }) =>
        geometriesApi
          .upload(name, values.description || null, folderId, file, (pct) =>
            updateUploadProgress(tempId, pct),
          )
          .then((data) => {
            removeJob(tempId);
            addJob(data.id, data.name, "stl_analysis");
            updateJob(data.id, "pending");
            return data;
          })
          .catch((e: Error) => {
            updateJob(tempId, "error", e.message);
            throw e;
          }),
      ),
    );

    const succeeded = results.filter((r) => r.status === "fulfilled").length;
    const failed = results.filter((r) => r.status === "rejected").length;

    queryClient.invalidateQueries({ queryKey: ["geometries"] });

    if (failed === 0) {
      notifications.show({
        message: `${succeeded} 件のアップロード完了 — バックグラウンドで解析中`,
        color: "green",
      });
    } else {
      notifications.show({
        message: `${succeeded} 件成功 / ${failed} 件失敗`,
        color: failed === results.length ? "red" : "yellow",
      });
    }

    setUploading(false);
    form.reset();
    setSelectedFiles([]);
    if (fileRef.current) fileRef.current.value = "";
    onClose();
  }

  function handleClose() {
    if (!uploading) {
      onClose();
      form.reset();
      setSelectedFiles([]);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Upload STL Geometry" size="md">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <Stack gap={4}>
            <Text size="sm" fw={500}>
              STL ファイル <Text component="span" c="red">*</Text>
            </Text>
            <input
              ref={fileRef}
              type="file"
              accept=".stl"
              multiple
              style={{ fontSize: 14 }}
              disabled={uploading}
              onChange={handleFileChange}
            />
            <Text size="xs" c="dimmed">
              複数選択可。ファイル名（拡張子なし）がそのまま Geometry 名になります。
            </Text>
          </Stack>

          {selectedFiles.length > 0 && (
            <Stack gap={4}>
              <Group gap="xs">
                <Text size="xs" fw={500} c="dimmed">選択中:</Text>
                <Badge size="sm" variant="light">{selectedFiles.length} ファイル</Badge>
              </Group>
              <List
                size="xs"
                spacing={2}
                icon={
                  <ThemeIcon size={14} variant="light" color="blue" radius="xl">
                    <IconFile size={9} />
                  </ThemeIcon>
                }
              >
                {selectedFiles.map((f) => (
                  <List.Item key={f.name}>
                    <Text size="xs" ff="monospace">{stemName(f.name)}</Text>
                    <Text size="xs" c="dimmed" component="span"> ({(f.size / 1048576).toFixed(1)} MB)</Text>
                  </List.Item>
                ))}
              </List>
            </Stack>
          )}

          <Textarea
            label="説明（全ファイル共通・任意）"
            placeholder="Optional description"
            disabled={uploading}
            {...form.getInputProps("description")}
          />
          <Select
            label="フォルダ（全ファイル共通）"
            placeholder="— No folder —"
            data={folderOptions}
            clearable
            disabled={uploading}
            {...form.getInputProps("folderId")}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={handleClose} disabled={uploading}>
              キャンセル
            </Button>
            <Button type="submit" loading={uploading} disabled={uploading || selectedFiles.length === 0}>
              {uploading
                ? "アップロード中…"
                : selectedFiles.length > 1
                  ? `${selectedFiles.length} 件をアップロード`
                  : "アップロード"}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
