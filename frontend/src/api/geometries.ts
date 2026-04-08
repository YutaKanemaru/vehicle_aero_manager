import { client } from "./client";
import type { paths } from "./schema.d.ts";

// ─── Types ──────────────────────────────────────────────────────────────────

export type GeometryResponse =
  paths["/api/v1/geometries/"]["get"]["responses"]["200"]["content"]["application/json"][number];

export type AssemblyResponse =
  paths["/api/v1/assemblies/"]["get"]["responses"]["200"]["content"]["application/json"][number];

export type AssemblyCreate =
  paths["/api/v1/assemblies/"]["post"]["requestBody"]["content"]["application/json"];

export type AssemblyUpdate =
  paths["/api/v1/assemblies/{assembly_id}"]["patch"]["requestBody"]["content"]["application/json"];

// ─── Geometry API ────────────────────────────────────────────────────────────

export const geometriesApi = {
  list: (): Promise<GeometryResponse[]> =>
    client.get("/geometries/"),

  get: (id: string): Promise<GeometryResponse> =>
    client.get(`/geometries/${id}`),

  /** multipart/form-data アップロード */
  upload: (name: string, description: string | null, file: File): Promise<GeometryResponse> => {
    const form = new FormData();
    form.append("name", name);
    if (description) form.append("description", description);
    form.append("file", file);

    const token = localStorage.getItem("vam_token");
    return fetch("/api/v1/geometries/", {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      return res.json();
    });
  },

  delete: (id: string): Promise<void> =>
    client.delete(`/geometries/${id}`),
};

// ─── Assembly API ────────────────────────────────────────────────────────────

export const assembliesApi = {
  list: (): Promise<AssemblyResponse[]> =>
    client.get("/assemblies/"),

  get: (id: string): Promise<AssemblyResponse> =>
    client.get(`/assemblies/${id}`),

  create: (data: AssemblyCreate): Promise<AssemblyResponse> =>
    client.post("/assemblies/", data),

  update: (id: string, data: AssemblyUpdate): Promise<AssemblyResponse> =>
    client.patch(`/assemblies/${id}`, data),

  delete: (id: string): Promise<void> =>
    client.delete(`/assemblies/${id}`),

  addGeometry: (assemblyId: string, geometryId: string): Promise<AssemblyResponse> =>
    client.post(`/assemblies/${assemblyId}/geometries/${geometryId}`, {}),

  removeGeometry: (assemblyId: string, geometryId: string): Promise<AssemblyResponse> =>
    client.delete(`/assemblies/${assemblyId}/geometries/${geometryId}`),
};
