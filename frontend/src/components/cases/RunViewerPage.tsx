/**
 * RunViewerPage — full-page 3D viewer for a specific Run.
 * Route: /cases/:caseId/runs/:runId/viewer
 *
 * Opens in a new browser tab via window.open() from CaseDetailPage.
 * Reuses RunViewer (3-column: OverlayPanel | PartListPanel | SceneCanvas).
 */
import { Text, LoadingOverlay, Group, ThemeIcon, Center, Stack, Badge } from "@mantine/core";
import { IconAlertCircle } from "@tabler/icons-react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { runsApi, casesApi, type RunResponse } from "../../api/configurations";
import { RunViewer } from "./RunViewer";

export function RunViewerPage() {
  const { caseId, runId } = useParams<{ caseId: string; runId: string }>();

  const { data: caseData, isLoading: caseLoading } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId!),
    enabled: !!caseId,
  });

  const { data: runs = [], isLoading: runsLoading } = useQuery({
    queryKey: ["runs", caseId],
    queryFn: () => runsApi.list(caseId!),
    enabled: !!caseId,
  });

  const isLoading = caseLoading || runsLoading;
  const run: RunResponse | undefined = runs.find((r) => r.id === runId);

  if (isLoading) {
    return <LoadingOverlay visible />;
  }

  if (!run || !caseData) {
    return (
      <Center h="100vh">
        <Group gap="sm">
          <ThemeIcon color="red" variant="light">
            <IconAlertCircle size={18} />
          </ThemeIcon>
          <Text c="dimmed">Run not found.</Text>
        </Group>
      </Center>
    );
  }

  if (run.status !== "ready") {
    return (
      <Center h="100vh">
        <Stack align="center" gap="xs">
          <Badge color="yellow" size="lg">{run.status}</Badge>
          <Text c="dimmed" size="sm">
            Run is not ready yet. Generate XML first.
          </Text>
        </Stack>
      </Center>
    );
  }

  return (
    <div style={{ height: "calc(100vh - 60px)" }}>
      <RunViewer
        caseId={caseId!}
        assemblyId={caseData.assembly_id}
        run={run}
      />
    </div>
  );
}
