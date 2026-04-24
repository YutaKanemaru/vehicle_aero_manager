/**
 * Preview API client — overlay data for the Template Builder 3D viewer.
 */

import { client } from "./client";
import type { paths } from "./schema.d.ts";

export type OverlayData =
  paths["/api/v1/preview/overlay"]["get"]["responses"]["200"]["content"]["application/json"];

export type OverlayBoxItem = OverlayData["refinement_boxes"][number];
export type OverlayPlaneItem = OverlayData["tg_planes"][number];
export type OverlayDomainPartItem = OverlayData["domain_parts"][number];
export type OverlayProbeItem = OverlayData["probes"][number];
export type OverlayPartsGroup = OverlayData["parts_groups"][number];

export const previewApi = {
  getOverlayData: (
    templateId: string,
    assemblyId: string,
  ): Promise<OverlayData> =>
    client
      .get("/api/v1/preview/overlay", {
        params: { template_id: templateId, assembly_id: assemblyId },
      })
      .then((r) => r.data),
};
