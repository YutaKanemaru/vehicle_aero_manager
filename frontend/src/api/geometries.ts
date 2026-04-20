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

export type AssemblyFolderResponse =
  paths["/api/v1/assemblies/folders/"]["get"]["responses"]["200"]["content"]["application/json"][number];

export type AssemblyFolderCreate =
  paths["/api/v1/assemblies/folders/"]["post"]["requestBody"]["content"]["application/json"];

export type AssemblyFolderUpdate =
  paths["/api/v1/assemblies/folders/{folder_id}"]["patch"]["requestBody"]["content"]["application/json"];

export type GeometryFolderResponse =
  paths["/api/v1/geometries/folders/"]["get"]["responses"]["200"]["content"]["application/json"][number];

export type GeometryFolderCreate =
  paths["/api/v1/geometries/folders/"]["post"]["requestBody"]["content"]["application/json"];

export type GeometryFolderUpdate =
  paths["/api/v1/geometries/folders/{folder_id}"]["patch"]["requestBody"]["content"]["application/json"];

export type GeometryLinkRequest =
  paths["/api/v1/geometries/link"]["post"]["requestBody"]["content"]["application/json"];

// ─── Assembly Folder API ─────────────────────────────────────────────────────

export const assemblyFoldersApi = {
  list: (): Promise<AssemblyFolderResponse[]> =>
    client.get("/assemblies/folders/"),

  create: (data: AssemblyFolderCreate): Promise<AssemblyFolderResponse> =>
    client.post("/assemblies/folders/", data),

  update: (id: string, data: AssemblyFolderUpdate): Promise<AssemblyFolderResponse> =>
    client.patch(`/assemblies/folders/${id}`, data),

  delete: (id: string): Promise<void> =>
    client.delete(`/assemblies/folders/${id}`),
};

// ─── Geometry Folder API ───────────────────────────────────────────────────

export const foldersApi = {
  list: (): Promise<GeometryFolderResponse[]> =>
    client.get("/geometries/folders/"),

  create: (data: GeometryFolderCreate): Promise<GeometryFolderResponse> =>
    client.post("/geometries/folders/", data),

  update: (id: string, data: GeometryFolderUpdate): Promise<GeometryFolderResponse> =>
    client.patch(`/geometries/folders/${id}`, data),

  delete: (id: string): Promise<void> =>
    client.delete(`/geometries/folders/${id}`),
};

// ─── Geometry API ────────────────────────────────────────────────────────────

export const geometriesApi = {
  list: (): Promise<GeometryResponse[]> =>
    client.get("/geometries/"),

  get: (id: string): Promise<GeometryResponse> =>
    client.get(`/geometries/${id}`),

  /** multipart/form-data アップロード (XHR to track upload progress) */
  upload: (
    name: string,
    description: string | null,
    folderId: string | null,
    file: File,
    onProgress?: (pct: number) => void,
  ): Promise<GeometryResponse> => {
    return new Promise((resolve, reject) => {
      const form = new FormData();
      form.append("name", name);
      if (description) form.append("description", description);
      if (folderId) form.append("folder_id", folderId);
      form.append("file", file);

      const token = localStorage.getItem("vam_token");
      const xhr = new XMLHttpRequest();

      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error("Invalid JSON response"));
          }
        } else {
          try {
            const body = JSON.parse(xhr.responseText);
            reject(new Error(body.detail || `HTTP ${xhr.status}`));
          } catch {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => reject(new Error("Network error"));
      xhr.onabort = () => reject(new Error("Upload aborted"));

      xhr.open("POST", "/api/v1/geometries/");
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.send(form);
    });
  },

  delete: (id: string): Promise<void> =>
    client.delete(`/geometries/${id}`),

  /** サーバーパスのみ登録（Link only モード）*/
  link: (data: GeometryLinkRequest): Promise<GeometryResponse> =>
    client.post("/geometries/link", data),

  updateFolder: (id: string, folderId: string | null): Promise<GeometryResponse> =>
    client.patch(`/geometries/${id}`, { folder_id: folderId }),

  /**
   * geometryのGLBをフェッチしてBlobURLを返す。
   * Three.jsのローダーに渡せるURL形式で返す。
   * 呼び出し側でURL.revokeObjectURL()すること。
   */
  getGlbBlobUrl: async (id: string, ratio: number = 0.5): Promise<string> => {
    const token = localStorage.getItem("vam_token");
    const res = await fetch(`/api/v1/geometries/${id}/glb?ratio=${ratio}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`GLB fetch failed: HTTP ${res.status}`);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },
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
