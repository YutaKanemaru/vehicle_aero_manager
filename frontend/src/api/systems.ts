import { client } from "./client";
import type { components } from "./schema";

// ---- Type exports --------------------------------------------------------

export type SystemResponse = components["schemas"]["SystemResponse"];
export type RideHeightConditionConfig =
  components["schemas"]["RideHeightConditionConfig"];
export type YawConditionConfig = components["schemas"]["YawConditionConfig"];
export type TransformRequest = components["schemas"]["TransformRequest"];

export interface TransformResult {
  system_id: string;
  geometry_id: string;
  geometry_name: string;
  geometry_status: string;
  transform_snapshot: Record<string, unknown> | null;
}

// ---- Systems API ---------------------------------------------------------

export const systemsApi = {
  list: (): Promise<SystemResponse[]> => client.get("/systems/"),

  get: (systemId: string): Promise<SystemResponse> =>
    client.get(`/systems/${systemId}`),

  delete: (systemId: string): Promise<void> =>
    client.delete(`/systems/${systemId}`),

  /** Fetch the landmarks GLB for a system. Returns a blob URL (caller must revokeObjectURL). */
  getLandmarksGlbUrl: async (systemId: string): Promise<string> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/systems/${systemId}/landmarks-glb`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return URL.createObjectURL(await res.blob());
  },
};

// ---- Geometry transform --------------------------------------------------

export const transformApi = {
  /** POST /geometries/{id}/transform — apply ride height + yaw transform. */
  transform: (
    geometryId: string,
    data: TransformRequest,
  ): Promise<TransformResult> =>
    client.post(`/geometries/${geometryId}/transform`, data),
};
