import { useEffect, useRef } from "react";
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
  const removeJob = useJobsStore((s) => s.removeJob);
  const prevHasActive = useRef(false);

  // Only poll when there are pending/analyzing/ready-decimating jobs (uploading is handled by XHR callbacks)
  const hasActive = jobs.some(
    (j) => j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating"
  );

  const interval = useInterval(async () => {
    const activeJobs = jobs.filter(
      (j) => j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating"
    );
    if (activeJobs.length === 0) return;

    try {
      const geometries = await geometriesApi.list();
      const gMap = new Map(geometries.map((g) => [g.id, g]));

      // pending/analyzing → ステータス更新、または削除済みなら除去
      for (const job of activeJobs) {
        const g = gMap.get(job.id);
        if (g) {
          updateJob(g.id, g.status as JobStatus, g.error_message);
        } else {
          // ジオメトリが削除済み → jobs からも削除
          removeJob(job.id);
        }
      }

      // ready/error ジョブも削除済みジオメトリなら除去（永続化されたゴミを掃除）
      const staleJobs = jobs.filter(
        (j) => (j.status === "ready" || j.status === "error") && !gMap.has(j.id)
      );
      for (const job of staleJobs) {
        removeJob(job.id);
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

  // hasActive が true→false になった瞬間に 1 回 stale job をクリーンアップする
  // (例: ジオメトリが削除されて ready/error ジョブが残っている場合)
  useEffect(() => {
    if (prevHasActive.current && !hasActive) {
      const staleIds = jobs
        .filter((j) => j.status === "ready" || j.status === "error")
        .map((j) => j.id);
      if (staleIds.length > 0) {
        geometriesApi.list().then((geometries) => {
          const liveIds = new Set(geometries.map((g) => g.id));
          staleIds.forEach((id) => {
            if (!liveIds.has(id)) removeJob(id);
          });
        }).catch(() => { /* silent */ });
      }
    }
    prevHasActive.current = hasActive;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasActive]);

  // アンマウント時に停止
  useEffect(() => () => interval.stop(), []);
}
