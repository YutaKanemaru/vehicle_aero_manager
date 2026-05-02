import { client } from "./client";
import type { components } from "./schema";
import type { OverlayData } from "./preview";

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
export type RunUpdate = components["schemas"]["RunUpdate"];

export type DiffResult = components["schemas"]["DiffResult"];
export type DiffField = components["schemas"]["DiffField"];
export type CaseCompareResult = components["schemas"]["CaseCompareResult"];
export type PartsDiffResult = components["schemas"]["PartsDiffResult"];

export type ConditionMapFolderResponse = components["schemas"]["ConditionMapFolderResponse"];
export type ConditionMapFolderCreate = components["schemas"]["ConditionMapFolderCreate"];
export type ConditionMapFolderUpdate = components["schemas"]["ConditionMapFolderUpdate"];

export type CaseFolderResponse = components["schemas"]["CaseFolderResponse"];
export type CaseFolderCreate = components["schemas"]["CaseFolderCreate"];
export type CaseFolderUpdate = components["schemas"]["CaseFolderUpdate"];

export type SyncRunsPreview = components["schemas"]["SyncRunsPreview"];
export type SyncRunsPreviewItem = components["schemas"]["SyncRunsPreviewItem"];

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

  compare: (caseId: string, withCaseId: string): Promise<CaseCompareResult> =>
    client.get(`/cases/${caseId}/compare?with=${withCaseId}`),

  syncPreview: (caseId: string, newMapId: string): Promise<SyncRunsPreview> =>
    client.get(`/cases/${caseId}/sync-preview?new_map_id=${encodeURIComponent(newMapId)}`),
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

  update: (caseId: string, runId: string, data: RunUpdate): Promise<RunResponse> =>
    client.patch(`/cases/${caseId}/runs/${runId}`, data),

  generate: (caseId: string, runId: string, geometryOnly = false): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/${runId}/generate?geometry_only=${geometryOnly}`, {}),

  delete: (caseId: string, runId: string): Promise<void> =>
    client.delete(`/cases/${caseId}/runs/${runId}`),

  reset: (caseId: string, runId: string): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/${runId}/reset`, {}),

  /** Generate 5-belt STL for a Run. Must be called before Transform/XML generation. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  generateBelts: (caseId: string, runId: string): Promise<any> =>
    client.post(`/cases/${caseId}/runs/${runId}/generate-belts`, {}),

  /** Apply ride-height + yaw transform for a Run. No body needed — backend derives all params. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  transform: (caseId: string, runId: string): Promise<any> =>
    client.post(`/cases/${caseId}/runs/${runId}/transform`, {}),

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

  downloadStl: async (caseId: string, runId: string): Promise<Blob> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/cases/${caseId}/runs/${runId}/download-stl`, {
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

  /** Fetch overlay data for a ready Run (parsed from its generated XML). */
  getOverlayData: (caseId: string, runId: string): Promise<OverlayData> =>
    client.get<OverlayData>(`/cases/${caseId}/runs/${runId}/overlay`),

  /** Fetch the belt GLB for a Run that has belt_stl_path set. Returns a blob URL (caller must revokeObjectURL). */
  getBeltGlbUrl: async (caseId: string, runId: string): Promise<string> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/cases/${caseId}/runs/${runId}/belt-glb`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return URL.createObjectURL(await res.blob());
  },
};
