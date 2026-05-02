import { useEffect, useRef } from "react";
import { useInterval } from "@mantine/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { geometriesApi } from "../api/geometries";
import { runsApi } from "../api/configurations";
import { useJobsStore, type JobStatus } from "../stores/jobs";

/**
 * AppLayout でマウントし続けることで、アクティブなジョブを 3 秒ごとにポーリングする。
 * pending / analyzing のジョブがなければインターバルは停止する。
 *
 * stl_analysis ジョブ: GET /geometries/ (list) でまとめて更新
 * stl_transform ジョブ: GET /geometries/{id} で個別取得 (listから除外されているため)
 */
export function useJobsPoller() {
  const jobs = useJobsStore((s) => s.jobs);
  const updateJob = useJobsStore((s) => s.updateJob);
  const removeJob = useJobsStore((s) => s.removeJob);
  const queryClient = useQueryClient();
  const prevHasActive = useRef(false);

  // Only poll when there are pending/analyzing/ready-decimating/generating jobs (uploading is handled by XHR callbacks)
  const hasActive = jobs.some(
    (j) => j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating" || j.status === "generating"
  );

  const interval = useInterval(async () => {
    const activeJobs = jobs.filter(
      (j) => j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating" || j.status === "generating"
    );
    if (activeJobs.length === 0) return;

    const analysisJobs = activeJobs.filter((j) => j.type === "stl_analysis");
    const transformJobs = activeJobs.filter((j) => j.type === "stl_transform");
    const xmlJobs = activeJobs.filter((j) => j.type === "xml_generation");

    // ── stl_analysis: list API でまとめて更新 ──────────────────────────────
    if (analysisJobs.length > 0) {
      try {
        const geometries = await geometriesApi.list();
        const gMap = new Map(geometries.map((g) => [g.id, g]));

        for (const job of analysisJobs) {
          const g = gMap.get(job.id);
          if (g) {
            updateJob(g.id, g.status as JobStatus, g.error_message);
          } else {
            removeJob(job.id);
          }
        }

        // ready/error stale cleanup for analysis jobs
        const staleAnalysis = jobs.filter(
          (j) => j.type === "stl_analysis" && (j.status === "ready" || j.status === "error") && !gMap.has(j.id)
        );
        for (const job of staleAnalysis) removeJob(job.id);
      } catch {
        // サイレント
      }
    }

    // ── stl_transform: 個別 GET で更新 (list から除外されているため) ───────
    if (transformJobs.length > 0) {
      await Promise.allSettled(
        transformJobs.map(async (job) => {
          try {
            const g = await geometriesApi.get(job.id);
            updateJob(g.id, g.status as JobStatus, g.error_message);
          } catch {
            // Geometry not found (deleted via reset/delete) → remove job from Drawer
            removeJob(job.id);
          }
        })
      );
    }

    // ── xml_generation: Run status ポーリング ────────────────────────────
    if (xmlJobs.length > 0) {
      await Promise.allSettled(
        xmlJobs.map(async (job) => {
          if (!job.caseId) return;
          try {
            const run = await runsApi.get(job.caseId, job.id);
            // Map run status → job status
            if (run.status === "ready" || run.status === "error") {
              updateJob(run.id, run.status as JobStatus, run.error_message ?? null);
              queryClient.invalidateQueries({ queryKey: ["runs", job.caseId] });
            }
            // "generating" stays as-is — keep polling
          } catch {
            // Run deleted → remove from Drawer
            removeJob(job.id);
          }
        })
      );
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
  useEffect(() => {
    if (prevHasActive.current && !hasActive) {
      // stl_analysis stale cleanup
      const staleAnalysisIds = jobs
        .filter((j) => j.type === "stl_analysis" && (j.status === "ready" || j.status === "error"))
        .map((j) => j.id);
      if (staleAnalysisIds.length > 0) {
        geometriesApi.list().then((geometries) => {
          const liveIds = new Set(geometries.map((g) => g.id));
          staleAnalysisIds.forEach((id) => {
            if (!liveIds.has(id)) removeJob(id);
          });
        }).catch(() => { /* silent */ });
      }

      // stl_transform stale cleanup — verify each individually
      const staleTransformJobs = jobs.filter(
        (j) => j.type === "stl_transform" && (j.status === "ready" || j.status === "error")
      );
      for (const job of staleTransformJobs) {
        geometriesApi.get(job.id).catch(() => removeJob(job.id));
      }
    }
    prevHasActive.current = hasActive;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasActive]);

  // アンマウント時に停止
  useEffect(() => () => interval.stop(), []);
}
