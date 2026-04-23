import { create } from "zustand";

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
  landmarks: boolean;
  probeSpheres: boolean;
  partialVolumes: boolean;
  sectionCuts: boolean;
}

interface ViewerStore {
  // Assembly selection
  selectedAssemblyId: string | null;
  setSelectedAssemblyId: (id: string | null) => void;

  // Template selection for overlays
  selectedTemplateId: string | null;
  setSelectedTemplateId: (id: string | null) => void;

  // Run selection for axes-GLB overlay
  selectedCaseId: string | null;
  setSelectedCaseId: (id: string | null) => void;
  selectedRunId: string | null;
  setSelectedRunId: (id: string | null) => void;
  axesGlbUrl: string | null;
  setAxesGlbUrl: (url: string | null) => void;

  // Decimation ratio (fraction to keep, 0.01–1.0)
  ratio: number;
  setRatio: (ratio: number) => void;

  // Part visibility/color/opacity — keyed by part name
  partStates: Record<string, PartState>;
  setPartState: (name: string, state: Partial<PartState>) => void;
  initParts: (names: string[]) => void;
  resetParts: () => void;
  showAllParts: () => void;

  // Search
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  searchMode: SearchMode;
  setSearchMode: (mode: SearchMode) => void;

  // Overlays
  overlays: ViewerOverlays;
  setOverlay: (key: keyof ViewerOverlays, value: boolean) => void;

  // Per-item overlay visibility — key: "domain_box" | "ground_plane" | "box_{name}" | "pv_{name}" | "sc_{name}" | "probe_{name}"
  // Default: true (visible) when key is absent
  overlayVisibility: Record<string, boolean>;
  setOverlayVisibility: (key: string, value: boolean) => void;

  // Camera
  cameraProjection: "perspective" | "orthographic";
  setCameraProjection: (p: "perspective" | "orthographic") => void;
  cameraPreset: string | null;  // trigger: "top" | "front" | "side" | "iso" | null
  setCameraPreset: (p: string | null) => void;

  // Viewer theme
  viewerTheme: "dark" | "light";
  setViewerTheme: (t: "dark" | "light") => void;

  // Shading options
  flatShading: boolean;
  setFlatShading: (v: boolean) => void;
  showEdges: boolean;
  setShowEdges: (v: boolean) => void;

  // Origin axes + XY plane overlay
  showOriginAxes: boolean;
  setShowOriginAxes: (v: boolean) => void;

  // Master overlay visibility (hides ALL template overlays in SceneCanvas)
  overlaysAllVisible: boolean;
  setOverlaysAllVisible: (v: boolean) => void;

  // Part selection (click highlight)
  selectedPartName: string | null;
  setSelectedPartName: (name: string | null) => void;

  // Fit camera to part
  fitToTarget: { center: [number, number, number]; radius: number } | null;
  setFitToTarget: (t: { center: [number, number, number]; radius: number } | null) => void;

  // Ride height transform — condition selection
  selectedConditionMapId: string | null;
  setSelectedConditionMapId: (id: string | null) => void;
  selectedConditionId: string | null;
  setSelectedConditionId: (id: string | null) => void;

  // Landmarks GLB overlay (transform result)
  landmarksGlbUrl: string | null;
  setLandmarksGlbUrl: (url: string | null) => void;
}

export const useViewerStore = create<ViewerStore>((set, get) => ({
  selectedAssemblyId: null,
  setSelectedAssemblyId: (id) => set({ selectedAssemblyId: id }),

  selectedTemplateId: null,
  setSelectedTemplateId: (id) => set({ selectedTemplateId: id }),

  selectedCaseId: null,
  setSelectedCaseId: (id) => set({ selectedCaseId: id }),
  selectedRunId: null,
  setSelectedRunId: (id) => set({ selectedRunId: id }),
  axesGlbUrl: null,
  setAxesGlbUrl: (url) => set({ axesGlbUrl: url }),

  ratio: 0.05,
  setRatio: (ratio) => set({ ratio }),

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
  showAllParts: () =>
    set((s) => ({
      partStates: Object.fromEntries(
        Object.entries(s.partStates).map(([k, v]) => [k, { ...v, visible: true }])
      ),
    })),

  searchQuery: "",
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  searchMode: "include",
  setSearchMode: (searchMode) => set({ searchMode }),

  overlays: {
    domainBox: true,
    refinementBoxes: false,
    wheelAxes: false,
    groundPlane: true,
    landmarks: true,
    probeSpheres: false,
    partialVolumes: false,
    sectionCuts: false,
  },
  setOverlay: (key, value) =>
    set((s) => ({ overlays: { ...s.overlays, [key]: value } })),

  overlayVisibility: {},
  setOverlayVisibility: (key, value) =>
    set((s) => ({ overlayVisibility: { ...s.overlayVisibility, [key]: value } })),

  cameraProjection: "perspective",
  setCameraProjection: (p) => set({ cameraProjection: p }),
  cameraPreset: null,
  setCameraPreset: (p) => set({ cameraPreset: p }),

  viewerTheme: "dark",
  setViewerTheme: (t) => set({ viewerTheme: t }),

  flatShading: false,
  setFlatShading: (v) => set({ flatShading: v }),
  showEdges: false,
  setShowEdges: (v) => set({ showEdges: v }),

  showOriginAxes: true,
  setShowOriginAxes: (v) => set({ showOriginAxes: v }),

  overlaysAllVisible: true,
  setOverlaysAllVisible: (v) => set({ overlaysAllVisible: v }),

  selectedPartName: null,
  setSelectedPartName: (name) => set({ selectedPartName: name }),

  fitToTarget: null,
  setFitToTarget: (t) => set({ fitToTarget: t }),

  selectedConditionMapId: null,
  setSelectedConditionMapId: (id) => set({ selectedConditionMapId: id }),
  selectedConditionId: null,
  setSelectedConditionId: (id) => set({ selectedConditionId: id }),

  landmarksGlbUrl: null,
  setLandmarksGlbUrl: (url) => set({ landmarksGlbUrl: url }),
}));
