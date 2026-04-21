import { client } from "./client";
import type { components } from "./schema";

// ---- Type exports --------------------------------------------------------

export type ConditionMapResponse =
  components["schemas"]["ConditionMapResponse"];
export type ConditionMapCreate =
  components["schemas"]["ConditionMapCreate"];
export type ConditionMapUpdate =
  components["schemas"]["ConditionMapUpdate"];

export type ConditionResponse = components["schemas"]["ConditionResponse"];
export type ConditionCreate = components["schemas"]["ConditionCreate"];
export type ConditionUpdate = components["schemas"]["ConditionUpdate"];

export type CaseResponse = components["schemas"]["CaseResponse"];
export type CaseCreate = components["schemas"]["CaseCreate"];
export type CaseUpdate = components["schemas"]["CaseUpdate"];
export type CaseDuplicateRequest = components["schemas"]["CaseDuplicateRequest"];

export type RunResponse = components["schemas"]["RunResponse"];
export type RunCreate = components["schemas"]["RunCreate"];

export type DiffResult = components["schemas"]["DiffResult"];

export type ConditionMapFolderResponse = components["schemas"]["ConditionMapFolderResponse"];
export type ConditionMapFolderCreate = components["schemas"]["ConditionMapFolderCreate"];
export type ConditionMapFolderUpdate = components["schemas"]["ConditionMapFolderUpdate"];

export type CaseFolderResponse = components["schemas"]["CaseFolderResponse"];
export type CaseFolderCreate = components["schemas"]["CaseFolderCreate"];
export type CaseFolderUpdate = components["schemas"]["CaseFolderUpdate"];

// ---- ConditionMap API ---------------------------------------------------

export const mapsApi = {
  list: (): Promise<ConditionMapResponse[]> =>
    client.get("/maps/"),

  get: (mapId: string): Promise<ConditionMapResponse> =>
    client.get(`/maps/${mapId}`),

  create: (data: ConditionMapCreate): Promise<ConditionMapResponse> =>
    client.post("/maps/", data),

  update: (mapId: string, data: ConditionMapUpdate): Promise<ConditionMapResponse> =>
    client.patch(`/maps/${mapId}`, data),

  delete: (mapId: string): Promise<void> =>
    client.delete(`/maps/${mapId}`),

  updateFolder: (mapId: string, folderId: string | null): Promise<ConditionMapResponse> =>
    client.patch(`/maps/${mapId}`, { folder_id: folderId }),
};

// ---- ConditionMap Folder API --------------------------------------------

export const mapFoldersApi = {
  list: (): Promise<ConditionMapFolderResponse[]> =>
    client.get("/maps/folders/"),

  create: (data: ConditionMapFolderCreate): Promise<ConditionMapFolderResponse> =>
    client.post("/maps/folders/", data),

  update: (folderId: string, data: ConditionMapFolderUpdate): Promise<ConditionMapFolderResponse> =>
    client.patch(`/maps/folders/${folderId}`, data),

  delete: (folderId: string): Promise<void> =>
    client.delete(`/maps/folders/${folderId}`),
};

// ---- Condition API ------------------------------------------------------

export const conditionsApi = {
  list: (mapId: string): Promise<ConditionResponse[]> =>
    client.get(`/maps/${mapId}/conditions/`),

  get: (mapId: string, conditionId: string): Promise<ConditionResponse> =>
    client.get(`/maps/${mapId}/conditions/${conditionId}`),

  create: (mapId: string, data: ConditionCreate): Promise<ConditionResponse> =>
    client.post(`/maps/${mapId}/conditions/`, data),

  update: (
    mapId: string,
    conditionId: string,
    data: ConditionUpdate,
  ): Promise<ConditionResponse> =>
    client.patch(`/maps/${mapId}/conditions/${conditionId}`, data),

  delete: (mapId: string, conditionId: string): Promise<void> =>
    client.delete(`/maps/${mapId}/conditions/${conditionId}`),
};

// ---- Case API -----------------------------------------------------------

export const casesApi = {
  list: (): Promise<CaseResponse[]> =>
    client.get("/cases/"),

  get: (caseId: string): Promise<CaseResponse> =>
    client.get(`/cases/${caseId}`),

  create: (data: CaseCreate, withRuns = false): Promise<CaseResponse> =>
    client.post(`/cases/?with_runs=${withRuns}`, data),

  update: (caseId: string, data: CaseUpdate): Promise<CaseResponse> =>
    client.patch(`/cases/${caseId}`, data),

  delete: (caseId: string): Promise<void> =>
    client.delete(`/cases/${caseId}`),

  duplicate: (caseId: string, data: CaseDuplicateRequest): Promise<CaseResponse> =>
    client.post(`/cases/${caseId}/duplicate`, data),

  updateFolder: (caseId: string, folderId: string | null): Promise<CaseResponse> =>
    client.patch(`/cases/${caseId}`, { folder_id: folderId }),
};

// ---- Case Folder API ----------------------------------------------------

export const caseFoldersApi = {
  list: (): Promise<CaseFolderResponse[]> =>
    client.get("/cases/folders/"),

  create: (data: CaseFolderCreate): Promise<CaseFolderResponse> =>
    client.post("/cases/folders/", data),

  update: (folderId: string, data: CaseFolderUpdate): Promise<CaseFolderResponse> =>
    client.patch(`/cases/folders/${folderId}`, data),

  delete: (folderId: string): Promise<void> =>
    client.delete(`/cases/folders/${folderId}`),
};

// ---- Run API ------------------------------------------------------------

export const runsApi = {
  list: (caseId: string): Promise<RunResponse[]> =>
    client.get(`/cases/${caseId}/runs/`),

  create: (caseId: string, data: RunCreate): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/`, data),

  generate: (caseId: string, runId: string): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/${runId}/generate`, {}),

  download: async (caseId: string, runId: string): Promise<Blob> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/cases/${caseId}/runs/${runId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.blob();
  },

  diff: (runIdA: string, runIdB: string): Promise<DiffResult> =>
    client.get(`/runs/diff?a=${runIdA}&b=${runIdB}`),

  /** Fetch the axes-GLB for a ready Run. Returns a blob URL (caller must revokeObjectURL). */
  getAxesGlbUrl: async (caseId: string, runId: string): Promise<string> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/cases/${caseId}/runs/${runId}/axes-glb`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return URL.createObjectURL(await res.blob());
  },
};
