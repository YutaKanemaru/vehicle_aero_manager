import { useEffect } from "react";
import { useInterval } from "@mantine/hooks";
import { geometriesApi } from "../api/geometries";
import { useJobsStore, type JobStatus } from "../stores/jobs";

/**
 * AppLayout でマウントし続けることで、アクティブなジョブを 3 秒ごとにポーリングする。
 * pending / analyzing のジョブがなければインターバルは停止する。
 */
export function useJobsPoller() {
  const jobs = useJobsStore((s) => s.jobs);
  const updateJob = useJobsStore((s) => s.updateJob);

  // Only poll when there are pending/analyzing jobs (uploading is handled by XHR callbacks)
  const hasActive = jobs.some(
    (j) => j.status === "pending" || j.status === "analyzing"
  );

  const interval = useInterval(async () => {
    const activeJobs = jobs.filter(
      (j) => j.status === "pending" || j.status === "analyzing"
    );
    if (activeJobs.length === 0) return;

    try {
      const geometries = await geometriesApi.list();
      const gMap = new Map(geometries.map((g) => [g.id, g]));
      for (const job of activeJobs) {
        const g = gMap.get(job.id);
        if (g) {
          updateJob(g.id, g.status as JobStatus, g.error_message);
        }
      }
    } catch {
      // ポーリングエラーは無視（サイレント）
    }
  }, 3000);

  useEffect(() => {
    if (hasActive) {
      interval.start();
    } else {
      interval.stop();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasActive]);

  // アンマウント時に停止
  useEffect(() => () => interval.stop(), []);
}
