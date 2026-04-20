import { useState } from "react";
import {
  Modal,
  TextInput,
  Textarea,
  Select,
  Button,
  Group,
  Stack,
  Text,
  Alert,
  Slider,
  Badge,
  Box,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { IconLink, IconAlertCircle } from "@tabler/icons-react";
import { geometriesApi, foldersApi } from "../../api/geometries";
import { useJobsStore } from "../../stores/jobs";

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function GeometryLinkModal({ opened, onClose }: Props) {
  const queryClient = useQueryClient();
  const addJob = useJobsStore((s) => s.addJob);
  const updateJob = useJobsStore((s) => s.updateJob);
  const [error, setError] = useState<string | null>(null);

  const { data: folders = [] } = useQuery({
    queryKey: ["geometry-folders"],
    queryFn: () => foldersApi.list(),
    enabled: opened,
  });

  const form = useForm({
    initialValues: {
      name: "",
      description: "",
      file_path: "",
      folder_id: null as string | null,
      decimationRatio: 0.05,
    },
    validate: {
      name: (v) => (v.trim() ? null : "名前は必須です"),
      file_path: (v) => (v.trim() ? null : "ファイルパスは必須です"),
    },
  });

  const linkMutation = useMutation({
    mutationFn: () =>
      geometriesApi.link({
        name: form.values.name.trim(),
        description: form.values.description.trim() || null,
        file_path: form.values.file_path.trim(),
        folder_id: form.values.folder_id || null,
        decimation_ratio: form.values.decimationRatio,
      }),
    onSuccess: (geometry) => {
      // 解析ジョブをトラッカーに登録
      addJob(geometry.id, geometry.name, "stl_analysis");
      updateJob(geometry.id, "pending");

      queryClient.invalidateQueries({ queryKey: ["geometries"] });
      onClose();
      form.reset();
      setError(null);
    },
    onError: (e: Error) => {
      setError(e.message);
    },
  });

  const handleClose = () => {
    if (!linkMutation.isPending) {
      onClose();
      form.reset();
      setError(null);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="STL をリンク（Link only）"
      size="md"
    >
      <Stack gap="md">
        <Alert
          icon={<IconAlertCircle size={16} />}
          color="blue"
          variant="light"
        >
          <Text size="sm">
            ファイルはコピーされません。バックエンドコンテナからアクセス可能なサーバーパスを指定してください。
            Docker 環境の場合は、ボリュームマウントされたパスが必要です。
          </Text>
        </Alert>

        <TextInput
          label="名前"
          placeholder="例: CX1_v1.2_AERO"
          required
          disabled={linkMutation.isPending}
          {...form.getInputProps("name")}
        />

        <Textarea
          label="説明"
          placeholder="任意"
          rows={2}
          disabled={linkMutation.isPending}
          {...form.getInputProps("description")}
        />

        <TextInput
          label="ファイルパス（サーバー上の絶対パス）"
          placeholder="/data/stl/vehicle/CX1_v1.2.stl"
          required
          disabled={linkMutation.isPending}
          {...form.getInputProps("file_path")}
        />

        <Select
          label="フォルダ（任意）"
          placeholder="フォルダなし"
          clearable
          data={folders.map((f) => ({ value: f.id, label: f.name }))}
          disabled={linkMutation.isPending}
          value={form.values.folder_id}
          onChange={(v) => form.setFieldValue("folder_id", v)}
        />

        <Stack gap={6}>
          <Group justify="space-between" align="center">
            <Text size="sm" fw={500}>3D Preview Quality</Text>
            {form.values.decimationRatio >= 1.0 ? (
              <Badge color="yellow" variant="light">Skip — no 3D preview</Badge>
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
                { value: 1.0, label: "Skip" },
              ]}
              label={(v) => v >= 1.0 ? "Skip" : `${Math.round(v * 100)}%`}
              disabled={linkMutation.isPending}
            />
          </Box>
          {form.values.decimationRatio >= 1.0 && (
            <Text size="xs" c="orange">
              3D preview will not be generated. The geometry cannot be viewed in the 3D viewer.
            </Text>
          )}
        </Stack>

        {error && (
          <Text c="red" size="sm">
            {error}
          </Text>
        )}

        <Group justify="flex-end">
          <Button
            variant="default"
            onClick={handleClose}
            disabled={linkMutation.isPending}
          >
            キャンセル
          </Button>
          <Button
            leftSection={<IconLink size={16} />}
            loading={linkMutation.isPending}
            onClick={() => {
              const result = form.validate();
              if (!result.hasErrors) {
                setError(null);
                linkMutation.mutate();
              }
            }}
          >
            リンクして解析
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
