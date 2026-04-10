import { client } from "./client";
import type { paths, components } from "./schema";

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

export type RunResponse = components["schemas"]["RunResponse"];
export type RunCreate = components["schemas"]["RunCreate"];

export type DiffResult = components["schemas"]["DiffResult"];

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

  create: (data: CaseCreate): Promise<CaseResponse> =>
    client.post("/cases/", data),

  update: (caseId: string, data: CaseUpdate): Promise<CaseResponse> =>
    client.patch(`/cases/${caseId}`, data),

  delete: (caseId: string): Promise<void> =>
    client.delete(`/cases/${caseId}`),
};

// ---- Run API ------------------------------------------------------------

export const runsApi = {
  list: (caseId: string): Promise<RunResponse[]> =>
    client.get(`/cases/${caseId}/runs/`),

  create: (caseId: string, data: RunCreate): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/`, data),

  generate: (caseId: string, runId: string): Promise<RunResponse> =>
    client.post(`/cases/${caseId}/runs/${runId}/generate`, {}),

  downloadUrl: (caseId: string, runId: string): string =>
    `/api/v1/cases/${caseId}/runs/${runId}/download`,

  diff: (runIdA: string, runIdB: string): Promise<DiffResult> =>
    client.get(`/runs/diff?a=${runIdA}&b=${runIdB}`),
};
