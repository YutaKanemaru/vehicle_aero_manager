---
applyTo: "frontend/src/**"
---

# Frontend Coding Conventions

## API Client (`src/api/`)

The TypeScript API schema and form defaults are auto-generated from the FastAPI backend:

```bash
npm run generate-api
```

This runs 3 steps: FastAPI → `openapi.json` → `schema.d.ts` → `templateDefaults.ts`

Write typed wrappers in `src/api/`:

```typescript
// src/api/auth.ts
import { client } from "./client";
import type { paths } from "./schema.d.ts";

type MeResponse = paths["/api/v1/auth/me"]["get"]["responses"]["200"]["content"]["application/json"];

export const authApi = {
  me: (): Promise<MeResponse> => client.get("/api/v1/auth/me").then(r => r.data),
};
```

Rules:
- **Always use `schema.d.ts` types** — never write manual API types
- Run `npm run generate-api` after every backend schema change
- Never call `fetch()` or `axios` directly in components — use `src/api/` wrappers
- `templateDefaults.ts` and `schema.d.ts` are **auto-generated** — never edit manually

## Template Form Defaults (`src/api/templateDefaults.ts`)

Auto-generated via `npm run generate-api`. Contains `TemplateSettings().model_dump()` as TypeScript `as const`.

`useTemplateSettingsForm.ts` consumes this via `FORM_DEFAULTS` — single source of truth for all defaults.

**To change a default**: update the Pydantic model/`_aero_setup()`, then run `npm run generate-api`. Never hardcode numeric defaults in components.

## State Management

- **Server state**: TanStack Query (`useQuery`, `useMutation`) — for all API data
- **Client/UI state**: Zustand stores in `src/stores/` — for auth, UI preferences, 3D viewer state
- Do not use `useState` for data that comes from the API

## UI Components

- Use **Mantine v8** components for all UI (forms, tables, modals, notifications)
- Use `@tabler/icons-react` for icons
- Minimize custom CSS — prefer Mantine's style props and `style` API
- Forms: use `@mantine/form`'s `useForm` hook
- **Mantine v8 gotcha**: `Modal.NativeScrollArea` does not exist — omit `scrollAreaComponent` prop. Use `ScrollArea` component directly inside modal content if needed.

## UI Language

- **All user-facing text must be in English** — labels, placeholders, buttons, errors, tooltips, modal titles
- Code comments may be in English or Japanese

## Component Structure

```
src/components/
  auth/           # Login, registration pages
  layout/         # AppShell, navigation, JobsDrawer
  templates/      # Template CRUD (TemplateList, TemplateCreateModal, etc.)
  geometries/     # Geometry upload, link, list
  assemblies/     # Assembly CRUD
  maps/           # Condition Map + Condition CRUD
  cases/          # CaseList, CaseDetailPage, RunViewer
  viewer/         # 3D viewer components (SceneCanvas, OverlayObjects, PartListPanel, etc.)
```

## 3D Viewer Patterns

- `viewerStore` (Zustand) — all viewer state; `partColor(name)` for deterministic part colors
- `overlayVisibility: Record<string, boolean>` — key absent = visible by default
- `SceneCanvas` sub-controllers use `useFrame` + `getState()` (not `useEffect`) for immediate response
- `FitToPartController`: Orthographic mode must NOT divide by `camera.zoom` (oscillation bug)
- GLB fetching: `geometriesApi.getGlbBlobUrl(id, ratio)` → `URL.createObjectURL()`; caller must `revokeObjectURL()` on cleanup

## Folder/Sort Patterns

- Folder-grouped lists: `FolderSection` (Paper + Collapse) with uncategorized items shown last
- Sort: `useSortedItems` hook (name/created_at, asc/desc) with `SortTh` headers

## React Query Key Conventions

- Templates: `["templates"]`, `["templates", id]`, `["templates", id, "versions"]`
- Geometries: `["geometries"]`, `["geometry", id]`
- Assemblies: `["assemblies"]`, `["assembly", id]`
- Cases: `["cases"]`, `["case", id]`
- Runs: `["runs", caseId]`
- Overlay: `["preview", "overlay", templateId, assemblyId]`
