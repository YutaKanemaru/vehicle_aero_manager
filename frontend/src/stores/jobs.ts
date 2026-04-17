import { create } from "zustand";
import { persist } from "zustand/middleware";

export type JobType = "stl_analysis";
export type JobStatus = "uploading" | "pending" | "analyzing" | "ready-decimating" | "ready" | "error";

export interface Job {
  id: string;
  name: string;
  type: JobType;
  status: JobStatus;
  uploadProgress?: number; // 0-100, only meaningful when status === "uploading"
  error_message?: string | null;
  addedAt: number;
}

interface JobsState {
  jobs: Job[];
  addJob: (id: string, name: string, type: JobType) => void;
  updateJob: (id: string, status: JobStatus, error_message?: string | null) => void;
  updateUploadProgress: (id: string, progress: number) => void;
  removeJob: (id: string) => void;
  clearCompleted: () => void;
}

export const useJobsStore = create<JobsState>()(
  persist(
    (set) => ({
      jobs: [],

      addJob: (id, name, type) =>
        set((s) => ({
          jobs: [
            ...s.jobs.filter((j) => j.id !== id),
            { id, name, type, status: "uploading", uploadProgress: 0, addedAt: Date.now() },
          ],
        })),

      updateJob: (id, status, error_message) =>
        set((s) => ({
          jobs: s.jobs.map((j) =>
            j.id === id ? { ...j, status, error_message, uploadProgress: undefined } : j
          ),
        })),

      updateUploadProgress: (id, progress) =>
        set((s) => ({
          jobs: s.jobs.map((j) =>
            j.id === id ? { ...j, uploadProgress: progress } : j
          ),
        })),

      clearCompleted: () =>
        set((s) => ({
          jobs: s.jobs.filter((j) => j.status !== "ready" && j.status !== "error"),
        })),

      removeJob: (id) =>
        set((s) => ({ jobs: s.jobs.filter((j) => j.id !== id) })),
    }),
    {
      name: "vam-jobs",
      partialize: (s) => ({
        jobs: s.jobs.filter(
          (j) => Date.now() - j.addedAt < 24 * 60 * 60 * 1000
        ),
      }),
    }
  )
);

// セレクタ helpers
export const selectActiveJobs = (s: JobsState) =>
  s.jobs.filter((j) => j.status === "uploading" || j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating");

export const selectActiveCount = (s: JobsState) =>
  s.jobs.filter((j) => j.status === "uploading" || j.status === "pending" || j.status === "analyzing" || j.status === "ready-decimating").length;
