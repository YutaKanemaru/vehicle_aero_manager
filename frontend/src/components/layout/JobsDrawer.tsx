import {
  Drawer,
  Stack,
  Group,
  Text,
  Box,
  Badge,
  Progress,
  Button,
  ScrollArea,
  ThemeIcon,
  Divider,
} from "@mantine/core";
import {
  IconCheck,
  IconX,
  IconLoader,
  IconClock,
  IconTrash,
  IconUpload,
} from "@tabler/icons-react";
import { useJobsStore, type Job } from "../../stores/jobs";

// ─── ステータスごとの設定 ────────────────────────────────────────────────────

const statusConfig = {
  uploading: {
    label: "Uploading…",
    color: "cyan",
    progressValue: 0, // overridden by uploadProgress at render time
    animated: false,
    striped: false,
    icon: <IconUpload size={14} />,
  },
  pending: {
    label: "Pending",
    color: "yellow",
    progressValue: 15,
    animated: true,
    striped: false,
    icon: <IconClock size={14} />,
  },
  analyzing: {
    label: "Analyzing…",
    color: "blue",
    progressValue: 60,
    animated: true,
    striped: true,
    icon: <IconLoader size={14} />,
  },
  ready: {
    label: "Complete",
    color: "green",
    progressValue: 100,
    animated: false,
    striped: false,
    icon: <IconCheck size={14} />,
  },
  error: {
    label: "Failed",
    color: "red",
    progressValue: 100,
    animated: false,
    striped: false,
    icon: <IconX size={14} />,
  },
} as const;

const typeLabel: Record<string, string> = {
  stl_analysis: "STL Analysis",
};

// ─── JobRow ──────────────────────────────────────────────────────────────────

function JobRow({ job }: { job: Job }) {
  const cfg = statusConfig[job.status];
  const progressValue =
    job.status === "uploading" ? (job.uploadProgress ?? 0) : cfg.progressValue;

  return (
    <Box
      p="sm"
      style={{
        border: "1px solid var(--mantine-color-default-border)",
        borderRadius: 8,
      }}
    >
      <Group justify="space-between" mb={6}>
        <Box style={{ flex: 1, minWidth: 0 }}>
          <Text size="sm" fw={500} truncate>
            {job.name}
          </Text>
          <Text size="xs" c="dimmed">
            {typeLabel[job.type] ?? job.type}
          </Text>
        </Box>
        <Badge
          color={cfg.color}
          size="sm"
          leftSection={
            <ThemeIcon size={12} color={cfg.color} variant="transparent">
              {cfg.icon}
            </ThemeIcon>
          }
        >
          {job.status === "uploading" ? `${progressValue}%` : cfg.label}
        </Badge>
      </Group>

      <Progress
        value={progressValue}
        color={cfg.color}
        size="sm"
        animated={cfg.animated}
        striped={cfg.striped}
      />

      {job.status === "error" && job.error_message && (
        <Text size="xs" c="red" mt={4}>
          {job.error_message}
        </Text>
      )}
    </Box>
  );
}

// ─── JobsDrawer ──────────────────────────────────────────────────────────────

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function JobsDrawer({ opened, onClose }: Props) {
  const jobs = useJobsStore((s) => s.jobs);
  const clearCompleted = useJobsStore((s) => s.clearCompleted);

  // 新しい順に並べる
  const sorted = [...jobs].sort((a, b) => b.addedAt - a.addedAt);
  const activeJobs = sorted.filter(
    (j) => j.status === "uploading" || j.status === "pending" || j.status === "analyzing"
  );
  const doneJobs = sorted.filter(
    (j) => j.status === "ready" || j.status === "error"
  );
  const hasCompleted = doneJobs.length > 0;

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="xs">
          <Text fw={600}>Background Jobs</Text>
          {activeJobs.length > 0 && (
            <Badge color="blue" size="sm" circle>
              {activeJobs.length}
            </Badge>
          )}
        </Group>
      }
      position="right"
      size="sm"
    >
      <Stack>
        {jobs.length === 0 && (
          <Text size="sm" c="dimmed" ta="center" py="xl">
            No background jobs yet.
          </Text>
        )}

        {activeJobs.length > 0 && (
          <Stack gap="xs">
            <Text size="xs" c="dimmed" fw={500} tt="uppercase">
              In Progress
            </Text>
            {activeJobs.map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
          </Stack>
        )}

        {activeJobs.length > 0 && doneJobs.length > 0 && <Divider />}

        {doneJobs.length > 0 && (
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="xs" c="dimmed" fw={500} tt="uppercase">
                Completed
              </Text>
              {hasCompleted && (
                <Button
                  size="xs"
                  variant="subtle"
                  color="gray"
                  leftSection={<IconTrash size={12} />}
                  onClick={clearCompleted}
                >
                  Clear
                </Button>
              )}
            </Group>
            <ScrollArea h={320}>
              <Stack gap="xs">
                {doneJobs.map((job) => (
                  <JobRow key={job.id} job={job} />
                ))}
              </Stack>
            </ScrollArea>
          </Stack>
        )}
      </Stack>
    </Drawer>
  );
}
