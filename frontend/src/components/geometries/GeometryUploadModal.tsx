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
  Slider,
  Switch,
  Box,
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
    initialValues: { description: "", folderId: "", decimationRatio: 0.05, skipGlb: false },
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
    const filesToUpload = [...selectedFiles];

    // ジョブをドロワーに登録
    const jobs = filesToUpload.map((file) => {
      const tempId = `tmp-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const name = stemName(file.name);
      addJob(tempId, name, "stl_analysis");
      return { tempId, name, file };
    });

    // モーダルを即座に閉じる — 転送はバックグラウンドで継続
    form.reset();
    setSelectedFiles([]);
    if (fileRef.current) fileRef.current.value = "";
    onClose();

    // 各ファイルのアップロードをバックグラウンドで実行
    jobs.forEach(({ tempId, name, file }) => {
      geometriesApi
        .upload(name, values.description || null, folderId, file, (pct) =>
          updateUploadProgress(tempId, pct),
          values.decimationRatio,
        )
        .then((data) => {
          removeJob(tempId);
          addJob(data.id, data.name, "stl_analysis");
          updateJob(data.id, "pending");
          queryClient.invalidateQueries({ queryKey: ["geometries"] });
        })
        .catch((e: Error) => {
          updateJob(tempId, "error", e.message);
        });
    });
  }

  function handleClose() {
    onClose();
    form.reset();
    setSelectedFiles([]);
    if (fileRef.current) fileRef.current.value = "";
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
            {...form.getInputProps("description")}
          />
          <Select
            label="フォルダ（全ファイル共通）"
            placeholder="— No folder —"
            data={folderOptions}
            clearable
            {...form.getInputProps("folderId")}
          />

          <Stack gap={6}>
            <Switch
              label="Skip 3D Preview"
              description="No GLB will be generated. The geometry cannot be viewed in the 3D viewer."
              checked={form.values.skipGlb}
              onChange={(e) => form.setFieldValue("skipGlb", e.currentTarget.checked)}
            />
            {!form.values.skipGlb && (
              <>
            <Group justify="space-between" align="center">
              <Text size="sm" fw={500}>3D Preview Quality</Text>
              {form.values.decimationRatio >= 1.0 ? (
                <Badge color="blue" variant="light">Full resolution — no decimation</Badge>
              ) : (
                <Badge color="blue" variant="light">
                  Keep {Math.round(form.values.decimationRatio * 100)}% of faces
                </Badge>
              )}
            </Group>
            <Box pb={24}>
              <Slider
                min={0.01}
                max={1.0}
                step={0.01}
                value={form.values.decimationRatio}
                onChange={(v) => form.setFieldValue("decimationRatio", v)}
                marks={[
                  { value: 0.05, label: "5%" },
                  { value: 0.25, label: "25%" },
                  { value: 0.5, label: "50%" },
                  { value: 1.0, label: "No Decimation" },
                ]}
                label={(v) => v >= 1.0 ? "No Decimation" : `${Math.round(v * 100)}%`}
              />
            </Box>
            {form.values.decimationRatio >= 1.0 && (
              <Text size="xs" c="dimmed">
                GLB will be generated at full resolution. May take longer and produce a larger file.
              </Text>
            )}
              </>
            )}
          </Stack>

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={handleClose}>
              キャンセル
            </Button>
            <Button type="submit" disabled={selectedFiles.length === 0}>
              {selectedFiles.length > 1
                ? `${selectedFiles.length} 件をアップロード`
                : "アップロード"}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
