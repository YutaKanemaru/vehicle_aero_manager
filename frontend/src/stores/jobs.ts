import { create } from "zustand";
import { persist } from "zustand/middleware";

export type JobType = "stl_analysis";
export type JobStatus = "pending" | "analyzing" | "ready" | "error";

export interface Job {
  id: string;
  name: string;
  type: JobType;
  status: JobStatus;
  error_message?: string | null;
  addedAt: number;
}

interface JobsState {
  jobs: Job[];
  addJob: (id: string, name: string, type: JobType) => void;
  updateJob: (id: string, status: JobStatus, error_message?: string | null) => void;
  clearCompleted: () => void;
}

export const useJobsStore = create<JobsState>()(
  persist(
    (set) => ({
      jobs: [],

  addJob: (id, name, type) =>
    set((s) => ({
      jobs: [
        // 同じ id が既にあれば置き換え
        ...s.jobs.filter((j) => j.id !== id),
        { id, name, type, status: "pending", addedAt: Date.now() },
      ],
    })),

  updateJob: (id, status, error_message) =>
    set((s) => ({
      jobs: s.jobs.map((j) =>
        j.id === id ? { ...j, status, error_message } : j
      ),
    })),

  clearCompleted: () =>
    set((s) => ({
      jobs: s.jobs.filter((j) => j.status !== "ready" && j.status !== "error"),
    })),
    }),
    {
      name: "vam-jobs",  // localStorage のキー名
      // リフレッシュ後、pending/analyzing はまだ実行中の可能性があるので保持
      // ready/error は保持しても問題ないが古くなりすぎたものは除外
      partialize: (s) => ({
        jobs: s.jobs.filter(
          (j) => Date.now() - j.addedAt < 24 * 60 * 60 * 1000  // 24時間以内のみ保持
        ),
      }),
    }
  )
);

export const selectActiveCount = (s: JobsState) =>
  s.jobs.filter((j) => j.status === "pending" || j.status === "analyzing").length;
