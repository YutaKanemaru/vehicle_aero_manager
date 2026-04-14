import { client } from "./client";
import type { paths } from "./schema.d.ts";

// ---------------------------------------------------------------------------
// Type aliases from generated schema
// ---------------------------------------------------------------------------

type TemplateResponse =
  paths["/api/v1/templates/"]["get"]["responses"]["200"]["content"]["application/json"][number];

type TemplateCreate =
  paths["/api/v1/templates/"]["post"]["requestBody"]["content"]["application/json"];

type TemplateUpdate =
  paths["/api/v1/templates/{template_id}"]["patch"]["requestBody"]["content"]["application/json"];

type TemplateVersionResponse =
  paths["/api/v1/templates/{template_id}/versions"]["get"]["responses"]["200"]["content"]["application/json"][number];

type TemplateVersionCreate =
  paths["/api/v1/templates/{template_id}/versions"]["post"]["requestBody"]["content"]["application/json"];

type TemplateVersionUpdate =
  paths["/api/v1/templates/{template_id}/versions/{version_id}"]["patch"]["requestBody"]["content"]["application/json"];

type TemplateForkRequest =
  paths["/api/v1/templates/{template_id}/fork"]["post"]["requestBody"]["content"]["application/json"];

type TemplateSettingsPreset =
  paths["/api/v1/templates/presets/{sim_type}"]["get"]["responses"]["200"]["content"]["application/json"];

type SettingsValidateRequest =
  paths["/api/v1/templates/validate-settings"]["post"]["requestBody"]["content"]["application/json"];

type SettingsValidateResponse =
  paths["/api/v1/templates/validate-settings"]["post"]["responses"]["200"]["content"]["application/json"];

// Re-export for consumers
export type {
  TemplateResponse,
  TemplateCreate,
  TemplateUpdate,
  TemplateVersionResponse,
  TemplateVersionCreate,
  TemplateVersionUpdate,
  TemplateForkRequest,
  TemplateSettingsPreset,
  SettingsValidateResponse,
};

// ---------------------------------------------------------------------------
// API wrappers
// ---------------------------------------------------------------------------

export const templatesApi = {
  list: (): Promise<TemplateResponse[]> =>
    client.get("/templates/"),

  get: (templateId: string): Promise<TemplateResponse> =>
    client.get(`/templates/${templateId}`),

  create: (data: TemplateCreate): Promise<TemplateResponse> =>
    client.post("/templates/", data),

  update: (templateId: string, data: TemplateUpdate): Promise<TemplateResponse> =>
    client.patch(`/templates/${templateId}`, data),

  delete: (templateId: string): Promise<void> =>
    client.delete(`/templates/${templateId}`),

  listVersions: (templateId: string): Promise<TemplateVersionResponse[]> =>
    client.get(`/templates/${templateId}/versions`),

  createVersion: (
    templateId: string,
    data: TemplateVersionCreate,
  ): Promise<TemplateVersionResponse> =>
    client.post(`/templates/${templateId}/versions`, data),

  activateVersion: (
    templateId: string,
    versionId: string,
  ): Promise<TemplateVersionResponse> =>
    client.patch(`/templates/${templateId}/versions/${versionId}/activate`, {}),

  updateVersion: (
    templateId: string,
    versionId: string,
    data: TemplateVersionUpdate,
  ): Promise<TemplateVersionResponse> =>
    client.patch(`/templates/${templateId}/versions/${versionId}`, data),

  fork: (
    templateId: string,
    data: TemplateForkRequest,
  ): Promise<TemplateResponse> =>
    client.post(`/templates/${templateId}/fork`, data),

  setHidden: (
    templateId: string,
    is_hidden: boolean,
  ): Promise<TemplateResponse> =>
    client.patch(`/templates/${templateId}/hide`, { is_hidden }),

  getPreset: (simType: string): Promise<TemplateSettingsPreset> =>
    client.get(`/templates/presets/${simType}`),

  validateSettings: (settings: Record<string, unknown>): Promise<SettingsValidateResponse> =>
    client.post("/templates/validate-settings", { settings }),
};
