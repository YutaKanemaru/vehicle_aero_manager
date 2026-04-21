import { Suspense, useEffect, useRef, useState } from "react";
import type React from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Grid, GizmoHelper, GizmoViewport } from "@react-three/drei";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { Center, Text } from "@mantine/core";
import { Loader } from "@mantine/core";
import { geometriesApi, type GeometryResponse } from "../../api/geometries";
import { useViewerStore } from "../../stores/viewerStore";
import { OverlayObjects, type VehicleBbox } from "./OverlayObjects";

// ─── GLB model inner component (rendered inside Suspense) ────────────────────

function GLBModel({
  blobUrl,
  parts,
}: {
  blobUrl: string;
  parts: string[];
}) {
  const { scene } = useGLTF(blobUrl);
  const { partStates, initParts, flatShading, showEdges } = useViewerStore();

  // パーツ名でstoreを初期化（1回のみ）
  useEffect(() => {
    if (parts.length > 0) initParts(parts);
  }, [parts.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  // partStates + flatShading の変化を3Dシーンへ反映
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      if (obj.userData?.isEdgeLine) return;
      const state = partStates[obj.name] ?? partStates[obj.parent?.name ?? ""];
      if (!state) return;

      obj.visible = state.visible;

      if (!(obj.material instanceof THREE.MeshStandardMaterial)) {
        obj.material = new THREE.MeshStandardMaterial();
      }
      const mat = obj.material as THREE.MeshStandardMaterial;
      mat.color.set(state.color);
      mat.opacity = state.opacity;
      mat.transparent = state.opacity < 1.0;
      mat.flatShading = flatShading;
      mat.needsUpdate = true;
    });
  }, [scene, partStates, flatShading]);

  // Edge lines visibility
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh) || obj.userData?.isEdgeLine) return;
      // Remove existing edge lines
      const existing = obj.children.filter((c) => c.userData?.isEdgeLine);
      existing.forEach((c) => obj.remove(c));
      if (showEdges) {
        const edges = new THREE.EdgesGeometry(obj.geometry, 15);
        const line = new THREE.LineSegments(
          edges,
          new THREE.LineBasicMaterial({ color: "#000000", opacity: 0.6, transparent: true })
        );
        line.userData.isEdgeLine = true;
        obj.add(line);
      }
    });
  }, [scene, showEdges]);

  return <primitive object={scene} />;
}

// カメラをメッシュ全体にフィット ──────────────────────────────────────────────

function CameraFitter({ blobUrl }: { blobUrl: string }) {
  const { camera, scene: threeScene } = useThree();
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current) return;
    // 少し待ってからfitする（GLBロード完了後）
    const timer = setTimeout(() => {
      const box = new THREE.Box3().setFromObject(threeScene);
      if (box.isEmpty()) return;
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      (camera as THREE.PerspectiveCamera).near = maxDim * 0.001;
      (camera as THREE.PerspectiveCamera).far = maxDim * 100;
      camera.position.set(center.x + maxDim * 1.5, center.y + maxDim * 0.8, center.z + maxDim * 1.5);
      camera.lookAt(center);
      (camera as THREE.PerspectiveCamera).updateProjectionMatrix();
      fitted.current = true;
    }, 300);
    return () => clearTimeout(timer);
  }, [blobUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Axes GLB overlay (wheel/porous axes from a Run) ────────────────────────

function AxesGLBModel({ blobUrl }: { blobUrl: string }) {
  const { scene } = useGLTF(blobUrl);
  // Axes are rendered as-is — no part-visibility management
  return <primitive object={scene} />;
}

// ─── Landmarks GLB overlay (ride-height transform before/after) ──────────────

function LandmarksGLBModel({ blobUrl }: { blobUrl: string }) {
  const { scene } = useGLTF(blobUrl);
  return <primitive object={scene} />;
}

// ─── Orthographic/Perspective camera switch ──────────────────────────────────

function CameraTypeController() {
  const { cameraProjection } = useViewerStore();
  const { camera, set, size } = useThree();
  const perspRef = useRef<THREE.PerspectiveCamera | null>(null);
  const orthoRef = useRef<THREE.OrthographicCamera | null>(null);
  const prevProjection = useRef<string>("perspective");

  useEffect(() => {
    if (cameraProjection === prevProjection.current) return;
    const aspect = size.width / size.height;

    if (cameraProjection === "orthographic") {
      if (!perspRef.current) perspRef.current = camera as THREE.PerspectiveCamera;

      const dist = camera.position.length();
      const fovRad = ((perspRef.current.fov ?? 45) * Math.PI) / 180;
      const halfH = Math.tan(fovRad / 2) * dist;
      const halfW = halfH * aspect;

      if (!orthoRef.current) {
        orthoRef.current = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 0.001, 10000);
      } else {
        orthoRef.current.left = -halfW;
        orthoRef.current.right = halfW;
        orthoRef.current.top = halfH;
        orthoRef.current.bottom = -halfH;
      }
      orthoRef.current.position.copy(camera.position);
      orthoRef.current.quaternion.copy(camera.quaternion);
      orthoRef.current.updateProjectionMatrix();
      set({ camera: orthoRef.current });
    } else {
      if (perspRef.current) {
        perspRef.current.position.copy(camera.position);
        perspRef.current.quaternion.copy(camera.quaternion);
        perspRef.current.updateProjectionMatrix();
        set({ camera: perspRef.current });
      }
    }
    prevProjection.current = cameraProjection;
  }, [cameraProjection]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Double-click pivot + right-click context menu ────────────────────────────

function PointerEventHandler({
  onContextMenu,
}: {
  onContextMenu: (x: number, y: number, partName: string | null) => void;
}) {
  const { camera, scene, controls, gl, raycaster } = useThree();

  useEffect(() => {
    const canvas = gl.domElement;

    const isMesh = (obj: THREE.Object3D): obj is THREE.Mesh =>
      obj instanceof THREE.Mesh && !obj.userData?.isEdgeLine;

    const getNDC = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      return new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1,
      );
    };

    const handleDblClick = (e: MouseEvent) => {
      if (!controls) return;
      raycaster.setFromCamera(getNDC(e), camera);
      const hits = raycaster.intersectObjects(scene.children, true).filter((h) => isMesh(h.object));
      if (hits.length > 0) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (controls as any).target?.copy(hits[0].point);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (controls as any).update?.();
      }
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      raycaster.setFromCamera(getNDC(e), camera);
      const hits = raycaster.intersectObjects(scene.children, true).filter((h) => isMesh(h.object));
      let partName: string | null = null;
      if (hits.length > 0) {
        const obj = hits[0].object;
        partName = obj.name || (obj.parent?.name ?? null);
        if (partName === "Scene" || partName === "") partName = null;
      }
      onContextMenu(e.clientX, e.clientY, partName);
    };

    canvas.addEventListener("dblclick", handleDblClick);
    canvas.addEventListener("contextmenu", handleContextMenu);
    return () => {
      canvas.removeEventListener("dblclick", handleDblClick);
      canvas.removeEventListener("contextmenu", handleContextMenu);
    };
  }, [camera, scene, controls, gl, raycaster, onContextMenu]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Right-click context menu (React DOM, outside Canvas) ────────────────────

const CTX_ITEM: React.CSSProperties = {
  display: "block",
  width: "100%",
  padding: "5px 14px",
  background: "none",
  border: "none",
  color: "#c1c2c5",
  fontSize: 12,
  cursor: "pointer",
  textAlign: "left",
};

function ContextMenuPanel({
  x, y, partName, onClose,
}: {
  x: number; y: number; partName: string | null; onClose: () => void;
}) {
  const { setPartState, resetParts } = useViewerStore();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  return (
    <div
      ref={ref}
      style={{
        position: "fixed", left: x, top: y, zIndex: 9999,
        background: "#25262b", border: "1px solid #444",
        borderRadius: 4, padding: "4px 0", minWidth: 140,
        boxShadow: "0 4px 12px rgba(0,0,0,0.6)",
      }}
    >
      {partName && (
        <div style={{ padding: "4px 14px", fontSize: 11, color: "#666", borderBottom: "1px solid #333", marginBottom: 2 }}>
          {partName}
        </div>
      )}
      {partName && (
        <button style={CTX_ITEM} onClick={() => { setPartState(partName, { visible: false }); onClose(); }}>
          Hide
        </button>
      )}
      <button style={CTX_ITEM} onClick={() => { resetParts(); onClose(); }}>
        Reset all
      </button>
    </div>
  );
}

// ─── Camera preset controller — watches store and repositions camera ───────────

function CameraPresetController() {
  const { cameraPreset, setCameraPreset } = useViewerStore();
  const { camera, scene: threeScene } = useThree();

  useEffect(() => {
    if (!cameraPreset) return;
    const box = new THREE.Box3().setFromObject(threeScene);
    if (box.isEmpty()) { setCameraPreset(null); return; }
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const dist = Math.max(size.x, size.y, size.z) * 2.0;

    const presets: Record<string, THREE.Vector3> = {
      iso:   new THREE.Vector3(center.x + dist, center.y + dist * 0.6, center.z + dist),
      front: new THREE.Vector3(center.x + dist * 1.5, center.y, center.z),
      side:  new THREE.Vector3(center.x, center.y - dist * 1.5, center.z),
      top:   new THREE.Vector3(center.x, center.y, center.z + dist * 1.5),
      rear:  new THREE.Vector3(center.x - dist * 1.5, center.y, center.z),
    };
    const pos = presets[cameraPreset];
    if (pos) {
      camera.position.copy(pos);
      camera.lookAt(center);
      (camera as THREE.PerspectiveCamera).updateProjectionMatrix?.();
    }
    setCameraPreset(null);
  }, [cameraPreset]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Public SceneCanvas component ────────────────────────────────────────────

interface SceneCanvasProps {
  geometries: GeometryResponse[];
  ratio: number;
  templateSettings?: Record<string, unknown> | null;
  vehicleBbox?: VehicleBbox | null;
}

interface BlobEntry {
  geometryId: string;
  url: string;
  parts: string[];
}

export function SceneCanvas({ geometries, ratio, templateSettings, vehicleBbox }: SceneCanvasProps) {
  const [blobEntries, setBlobEntries] = useState<BlobEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; partName: string | null } | null>(null);
  // Must be called unconditionally before any early returns
  const { axesGlbUrl, landmarksGlbUrl, overlays, viewerTheme } = useViewerStore();

  const handleContextMenu = (x: number, y: number, partName: string | null) => {
    setContextMenu({ x, y, partName });
  };

  const readyGeometries = geometries.filter((g) => g.status === "ready");

  // コンポーネントが geometries / lod が変化したら GLB を再フェッチ
  useEffect(() => {
    if (readyGeometries.length === 0) {
      setBlobEntries([]);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    // 既存 Blob URLs を解放
    setBlobEntries((prev) => {
      prev.forEach((e) => URL.revokeObjectURL(e.url));
      return [];
    });

    Promise.all(
      readyGeometries.map(async (g) => {
        const url = await geometriesApi.getGlbBlobUrl(g.id, ratio);
        const parts: string[] =
          (g.analysis_result as { parts?: string[] } | null)?.parts ?? [];
        return { geometryId: g.id, url, parts };
      })
    )
      .then((entries) => {
        if (!cancelled) {
          setBlobEntries(entries);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(String(e));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [readyGeometries.map((g) => g.id).join(","), ratio]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <Center h="100%">
        <Loader />
      </Center>
    );
  }

  if (error) {
    return (
      <Center h="100%">
        <Text c="red">{error}</Text>
      </Center>
    );
  }

  if (blobEntries.length === 0) {
    return (
      <Center h="100%">
        <Text c="dimmed">Select an assembly to view geometry</Text>
      </Center>
    );
  }

  const allParts = blobEntries.flatMap((e) => e.parts);
  void allParts; // used in PartListPanel via assembly parts list

  const bgColor = viewerTheme === "dark" ? "#1a1b1e" : "#e8e8e8";

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {contextMenu && (
        <ContextMenuPanel
          x={contextMenu.x}
          y={contextMenu.y}
          partName={contextMenu.partName}
          onClose={() => setContextMenu(null)}
        />
      )}
      <Canvas
        style={{ width: "100%", height: "100%" }}
        camera={{ position: [10, 5, 10], fov: 45 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={[bgColor]} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 20, 10]} intensity={1.0} />
        <directionalLight position={[-10, -5, -10]} intensity={0.3} />

        <Suspense fallback={null}>
          {blobEntries.map((entry) => (
            <GLBModel key={entry.geometryId} blobUrl={entry.url} parts={entry.parts} />
          ))}
          {axesGlbUrl && overlays.wheelAxes && (
            <AxesGLBModel blobUrl={axesGlbUrl} />
          )}
          {landmarksGlbUrl && overlays.landmarks && (
            <LandmarksGLBModel blobUrl={landmarksGlbUrl} />
          )}
          <CameraFitter blobUrl={blobEntries[0].url} />
        </Suspense>

        <CameraPresetController />
        <CameraTypeController />
        <PointerEventHandler onContextMenu={handleContextMenu} />

        <OverlayObjects
          templateSettings={templateSettings}
          vehicleBbox={vehicleBbox}
        />

        <Grid
          args={[200, 200]}
          cellSize={0.1}
          cellThickness={0.4}
          cellColor={viewerTheme === "dark" ? "#333" : "#aaa"}
          sectionSize={1}
          sectionThickness={0.8}
          sectionColor={viewerTheme === "dark" ? "#555" : "#888"}
          fadeDistance={120}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid
        />

        <OrbitControls makeDefault />

        <GizmoHelper alignment="bottom-left" margin={[60, 60]}>
          <GizmoViewport
            axisColors={["#ff4444", "#44bb44", "#4499ff"]}
            labelColor="white"
          />
        </GizmoHelper>
      </Canvas>
    </div>
  );
}
