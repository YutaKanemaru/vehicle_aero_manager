import { create } from "zustand";

export type Lod = "low" | "medium" | "high";
export type SearchMode = "include" | "exclude";

export interface PartState {
  visible: boolean;
  color: string;
  opacity: number;
}

export interface ViewerOverlays {
  domainBox: boolean;
  refinementBoxes: boolean;
  wheelAxes: boolean;
  groundPlane: boolean;
}

interface ViewerStore {
  // Assembly selection
  selectedAssemblyId: string | null;
  setSelectedAssemblyId: (id: string | null) => void;

  // Template selection for overlays
  selectedTemplateId: string | null;
  setSelectedTemplateId: (id: string | null) => void;

  // LOD
  lod: Lod;
  setLod: (lod: Lod) => void;

  // Part visibility/color/opacity — keyed by part name
  partStates: Record<string, PartState>;
  setPartState: (name: string, state: Partial<PartState>) => void;
  initParts: (names: string[]) => void;
  resetParts: () => void;

  // Search
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  searchMode: SearchMode;
  setSearchMode: (mode: SearchMode) => void;

  // Overlays
  overlays: ViewerOverlays;
  setOverlay: (key: keyof ViewerOverlays, value: boolean) => void;
}

export const useViewerStore = create<ViewerStore>((set, get) => ({
  selectedAssemblyId: null,
  setSelectedAssemblyId: (id) => set({ selectedAssemblyId: id }),

  selectedTemplateId: null,
  setSelectedTemplateId: (id) => set({ selectedTemplateId: id }),

  lod: "medium",
  setLod: (lod) => set({ lod }),

  partStates: {},
  setPartState: (name, state) =>
    set((s) => ({
      partStates: {
        ...s.partStates,
        [name]: { ...s.partStates[name], ...state },
      },
    })),
  initParts: (names) => {
    const current = get().partStates;
    const next: Record<string, PartState> = {};
    for (const name of names) {
      next[name] = current[name] ?? { visible: true, color: "#88aabb", opacity: 1.0 };
    }
    set({ partStates: next });
  },
  resetParts: () => set({ partStates: {} }),

  searchQuery: "",
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  searchMode: "include",
  setSearchMode: (searchMode) => set({ searchMode }),

  overlays: {
    domainBox: true,
    refinementBoxes: false,
    wheelAxes: false,
    groundPlane: true,
  },
  setOverlay: (key, value) =>
    set((s) => ({ overlays: { ...s.overlays, [key]: value } })),
}));
