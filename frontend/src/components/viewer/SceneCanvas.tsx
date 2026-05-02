import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useThree, useFrame } from "@react-three/fiber";
import { OrbitControls, Grid, GizmoHelper, GizmoViewport } from "@react-three/drei";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { Center, Text, Stack } from "@mantine/core";
import { Loader } from "@mantine/core";
import { geometriesApi, type GeometryResponse } from "../../api/geometries";
import { useViewerStore } from "../../stores/viewerStore";
import { partColor } from "../../stores/viewerStore";
import { OverlayObjects } from "./OverlayObjects";
import type { OverlayData } from "../../api/preview";

// ─── Helper: build Box3 from GLB meshes only (excludes Grid, axes, gizmos) ───
// Grid args={[200,200]} would dominate setFromObject(scene) for m-unit models.
// Tag every GLB mesh with userData.isGLBMesh=true, then use expandByObject only on those.
function buildGLBBox(scene: THREE.Object3D): THREE.Box3 {
  const box = new THREE.Box3();
  scene.traverse((obj) => {
    if ((obj as THREE.Mesh).isMesh && obj.userData.isGLBMesh) {
      box.expandByObject(obj);
    }
  });
  return box;
}

// ─── GLB model inner component (rendered inside Suspense) ────────────────────

function GLBModel({
  blobUrl,
  parts,
  rhRefActive,
}: {
  blobUrl: string;
  parts: string[];
  rhRefActive: boolean;
}) {
  const { scene } = useGLTF(blobUrl);
  const { partStates, initParts, flatShading, showEdges, selectedPartName, setGlbLoaded } = useViewerStore();

  // パーツ名でstoreを初期化（1回のみ）
  useEffect(() => {
    if (parts.length > 0) initParts(parts);
  }, [parts.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  // flatShading 専用 effect — ON/OFF のたびにマテリアルを再生成して WebGL シェーダーキャッシュをバイパス
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh) || obj.userData?.isEdgeLine) return;
      // Tag as GLB mesh so buildGLBBox can identify it (excludes Grid/axes/gizmos)
      obj.userData.isGLBMesh = true;
      const old = obj.material instanceof THREE.MeshStandardMaterial
        ? obj.material as THREE.MeshStandardMaterial
        : null;
      const next = new THREE.MeshStandardMaterial({
        flatShading,
        color: old?.color ?? new THREE.Color(partColor(obj.name)),
        opacity: old?.opacity ?? 1.0,
        transparent: old ? old.transparent : false,
        emissive: old?.emissive ?? new THREE.Color(0, 0, 0),
      });
      old?.dispose();
      obj.material = next;
    });
  }, [scene, flatShading]); // eslint-disable-line react-hooks/exhaustive-deps

  // partStates (色・不透明度・表示) + 選択ハイライトの変化を3Dシーンへ反映
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      if (obj.userData?.isEdgeLine) return;

      if (!(obj.material instanceof THREE.MeshStandardMaterial)) {
        obj.material = new THREE.MeshStandardMaterial({ flatShading });
      }
      const mat = obj.material as THREE.MeshStandardMaterial;

      if (rhRefActive) {
        // Dim: override all meshes to near-invisible
        obj.visible = true;
        mat.opacity = 0.15;
        mat.transparent = true;
        mat.needsUpdate = true;
        return;
      }

      const state = partStates[obj.name] ?? partStates[obj.parent?.name ?? ""];
      const partName = obj.name || obj.parent?.name || "";

      obj.visible = state ? state.visible : true;

      const isSelected = obj.name === selectedPartName || obj.parent?.name === selectedPartName;
      if (isSelected) {
        mat.color.set("#ffff00");
        if (!mat.emissive) mat.emissive = new THREE.Color(0, 0, 0);
        mat.emissive.set("#444400");
      } else {
        mat.color.set(state?.color ?? partColor(partName));
        if (mat.emissive) mat.emissive.set("#000000");
      }
      mat.opacity = state?.opacity ?? 1.0;
      mat.transparent = (state?.opacity ?? 1.0) < 1.0;
      mat.needsUpdate = true;
    });
  }, [scene, partStates, selectedPartName, rhRefActive]); // eslint-disable-line react-hooks/exhaustive-deps

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

  // GLB ロード完了を検知 — Mesh が1つでも存在したら glbLoaded=true をストアに通知
  useEffect(() => {
    let hasMesh = false;
    scene.traverse((obj) => { if ((obj as THREE.Mesh).isMesh) hasMesh = true; });
    if (hasMesh) setGlbLoaded(true);
  }, [scene]); // eslint-disable-line react-hooks/exhaustive-deps

  return <primitive object={scene} />;
}

// カメラをメッシュ全体にフィット ──────────────────────────────────────────────
// glbLoaded が true になった直後に1回だけ実行される（setTimeout不要）

function CameraFitter() {
  const { camera, scene: threeScene, controls } = useThree();
  const { glbLoaded } = useViewerStore();
  const fitted = useRef(false);

  // Assembly が切り替わったとき（glbLoaded が false に戻ったとき）fitted フラグをリセット
  useEffect(() => {
    if (!glbLoaded) fitted.current = false;
  }, [glbLoaded]);

  useEffect(() => {
    if (!glbLoaded || fitted.current) return;
    threeScene.updateMatrixWorld(true);
    const box = buildGLBBox(threeScene);
    if (box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    // Set near/far based on camera type
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.near = maxDim * 0.001;
      camera.far  = maxDim * 100;
    } else if (camera instanceof THREE.OrthographicCamera) {
      camera.near = -maxDim * 500;
      camera.far  =  maxDim * 500;
    }
    // Z-up: iso view from +X, -Y, +Z  (multiplier 1.2 ≈ 8m standoff for 5m vehicle)
    camera.up.set(0, 0, 1);
    camera.position.set(
      center.x + maxDim * 1.2,
      center.y - maxDim * 1.2,
      center.z + maxDim * 0.6,
    );
    camera.lookAt(center);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (controls as any)?.target?.copy(center);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (controls as any)?.update?.();
    camera.updateProjectionMatrix();
    fitted.current = true;
  }, [glbLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

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
  const { camera, set, size, controls } = useThree();
  const perspRef = useRef<THREE.PerspectiveCamera | null>(null);
  const orthoRef = useRef<THREE.OrthographicCamera | null>(null);
  // Initial prevProjection matches the Canvas default (PerspectiveCamera),
  // so the first render with cameraProjection="orthographic" immediately triggers a switch.
  const prevProjection = useRef<string>("perspective");

  useEffect(() => {
    if (cameraProjection === prevProjection.current) return;
    const aspect = size.width / size.height;
    // Preserve current controls target across the switch to avoid rotation snap
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const currentTarget = ((controls as any)?.target as THREE.Vector3 | undefined)
      ?.clone() ?? new THREE.Vector3();

    if (cameraProjection === "orthographic") {
      if (!perspRef.current) perspRef.current = camera as THREE.PerspectiveCamera;

      // Use distance from camera to orbit target (not to world origin)
      const dist = camera.position.distanceTo(currentTarget);
      const fovRad = ((perspRef.current.fov ?? 45) * Math.PI) / 180;
      const halfH = Math.tan(fovRad / 2) * dist;
      const halfW = halfH * aspect;
      // Use a large near/far range — negative near avoids front-clipping when zooming
      const farRange = Math.max(halfH, dist) * 500;

      if (!orthoRef.current) {
        orthoRef.current = new THREE.OrthographicCamera(
          -halfW, halfW, halfH, -halfH, -farRange, farRange
        );
      } else {
        orthoRef.current.left   = -halfW;
        orthoRef.current.right  =  halfW;
        orthoRef.current.top    =  halfH;
        orthoRef.current.bottom = -halfH;
        orthoRef.current.near   = -farRange;
        orthoRef.current.far    =  farRange;
      }
      orthoRef.current.up.copy(camera.up);
      orthoRef.current.position.copy(camera.position);
      orthoRef.current.quaternion.copy(camera.quaternion);
      orthoRef.current.updateProjectionMatrix();
      set({ camera: orthoRef.current });
    } else {
      if (perspRef.current) {
        perspRef.current.up.copy(camera.up);
        perspRef.current.position.copy(camera.position);
        perspRef.current.quaternion.copy(camera.quaternion);
        perspRef.current.updateProjectionMatrix();
        set({ camera: perspRef.current });
      }
    }
    // Re-apply target so OrbitControls doesn't snap/rotate on the next frame
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (controls as any)?.target?.copy(currentTarget);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (controls as any)?.update?.();
    prevProjection.current = cameraProjection;
  }, [cameraProjection]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Double-click pivot + right-click context menu ────────────────────────────

function PointerEventHandler() {
  const { camera, scene, controls, gl, raycaster } = useThree();
  const { setSelectedPartName } = useViewerStore();

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

    const handleClick = (e: MouseEvent) => {
      raycaster.setFromCamera(getNDC(e), camera);
      const hits = raycaster.intersectObjects(scene.children, true).filter((h) => isMesh(h.object));
      if (hits.length > 0) {
        const obj = hits[0].object;
        let name = obj.name || (obj.parent?.name ?? null);
        if (name === "Scene" || name === "") name = null;
        setSelectedPartName(name);
      } else {
        setSelectedPartName(null);
      }
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
      e.preventDefault(); // Prevent browser context menu on canvas
    };

    canvas.addEventListener("click", handleClick);
    canvas.addEventListener("dblclick", handleDblClick);
    canvas.addEventListener("contextmenu", handleContextMenu);
    return () => {
      canvas.removeEventListener("click", handleClick);
      canvas.removeEventListener("dblclick", handleDblClick);
      canvas.removeEventListener("contextmenu", handleContextMenu);
    };
  }, [camera, scene, controls, gl, raycaster, setSelectedPartName]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ─── Camera preset controller — watches store and repositions camera ───────────

function CameraPresetController() {
  const { camera, scene: threeScene, controls } = useThree();

  // useFrame — Zustand .getState() で毎フレーム礁読み￼ React render cycle に依存せず連打でも即応答
  useFrame(() => {
    const { cameraPreset, setCameraPreset } = useViewerStore.getState();
    if (!cameraPreset) return;

    threeScene.updateMatrixWorld(true);
    const box = buildGLBBox(threeScene);
    if (box.isEmpty()) { setCameraPreset(null); return; }
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    // dist multiplier を CameraFitter と揃時 (1.2) に統一 — 5m車両で約 8m 離れ
    const dist = Math.max(size.x, size.y, size.z) * 1.2;

    // Z-up: X=forward (downstream), Y=lateral, Z=up
    const presets: Record<string, THREE.Vector3> = {
      iso:   new THREE.Vector3(center.x + dist, center.y - dist * 0.6, center.z + dist * 0.6),
      front: new THREE.Vector3(center.x - dist * 1.5, center.y, center.z),
      rear:  new THREE.Vector3(center.x + dist * 1.5, center.y, center.z),
      side:  new THREE.Vector3(center.x, center.y - dist * 1.5, center.z),
      top:   new THREE.Vector3(center.x, center.y, center.z + dist * 1.5),
    };
    const pos = presets[cameraPreset];
    if (pos) {
      camera.up.set(0, 0, 1);
      camera.position.copy(pos);
      camera.lookAt(center);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.target?.copy(center);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.update?.();
      camera.updateProjectionMatrix();
    }
    setCameraPreset(null);
  });

  return null;
}

// ─── Orbit center marker — small white dot at controls.target ─────────────────

function OrbitCenterMarker() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { controls } = useThree();

  useFrame(() => {
    if (!meshRef.current || !controls) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const target = (controls as any).target as THREE.Vector3 | undefined;
    if (target) meshRef.current.position.copy(target);
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.04, 8, 8]} />
      <meshBasicMaterial color="#ffffff" opacity={0.85} transparent />
    </mesh>
  );
}

// ─── Fit camera to a part (triggered via store) ───────────────────────────────

function FitToPartController() {
  const { camera, controls } = useThree();

  // useFrame — Zustand .getState() で毎フレーム監視、連打でも即応答
  useFrame(() => {
    const { fitToTarget, setFitToTarget } = useViewerStore.getState();
    if (!fitToTarget) return;

    const center = new THREE.Vector3(...fitToTarget.center);
    const radius = fitToTarget.radius;
    camera.up.set(0, 0, 1);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const currentTarget = (controls as any)?.target as THREE.Vector3 | undefined;

    if (camera instanceof THREE.OrthographicCamera) {
      // Ortho: preserve viewing direction and distance, only shift target + adjust zoom.
      // IMPORTANT: set camera.position BEFORE controls.update() — otherwise OrbitControls
      // will recompute position from (old position → new target) and move the camera,
      // which shifts near/far and causes clipping artifacts.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const oldTarget = ((controls as any)?.target as THREE.Vector3 | undefined)?.clone()
        ?? new THREE.Vector3();
      const oldDist = camera.position.distanceTo(oldTarget);
      const dir = camera.position.clone().sub(oldTarget).normalize();
      camera.position.copy(center.clone().addScaledVector(dir, oldDist));
      // frustumHalfH is zoom=1 world-space half-height — fixed value, must NOT divide by camera.zoom
      // (dividing creates a feedback loop: zoom→recalc→zoom oscillates every other press)
      const frustumHalfH = (camera.top - camera.bottom) / 2;
      camera.zoom = (frustumHalfH / radius) * 0.8;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.target?.copy(center);
      camera.updateProjectionMatrix();
    } else {
      // Perspective: move camera along current viewing direction toward the part
      const dist = radius * 2.5;
      const dir = (currentTarget && camera.position.distanceTo(currentTarget) > 0.01)
        ? new THREE.Vector3().subVectors(camera.position, currentTarget).normalize()
        : new THREE.Vector3(0.45, -0.6, 0.45).normalize();
      camera.position.copy(center.clone().addScaledVector(dir, dist));
      camera.lookAt(center);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.target?.copy(center);
      camera.updateProjectionMatrix();
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (controls as any)?.update?.();
    setFitToTarget(null);
  });

  return null;
}

// ─── Local type for vehicle bounding box ─────────────────────────────────────
type VehicleBbox = { x_min: number; x_max: number; y_min: number; y_max: number; z_min: number; z_max: number };

// ─── Origin coordinate axes + XY ground plane ───────────────────────────────

function OriginAxes({ vehicleBbox }: { vehicleBbox?: VehicleBbox | null }) {
  // Axis length: 15% of vehicle max dimension, fallback 1 m
  const axisSize = vehicleBbox
    ? Math.max(
        vehicleBbox.x_max - vehicleBbox.x_min,
        vehicleBbox.y_max - vehicleBbox.y_min,
        vehicleBbox.z_max - vehicleBbox.z_min,
      ) * 0.15
    : 1.0;

  // XY plane half-extent: 2× vehicle footprint, fallback 5 m
  const planeSize = vehicleBbox
    ? Math.max(
        vehicleBbox.x_max - vehicleBbox.x_min,
        vehicleBbox.y_max - vehicleBbox.y_min,
      ) * 2.0
    : 10.0;

  return (
    <group>
      {/* Coordinate axes at origin — red=X, green=Y, blue=Z */}
      <axesHelper args={[axisSize]} />
      {/* Semi-transparent XY plane at z=0 */}
      <mesh rotation={[0, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[planeSize, planeSize]} />
        <meshBasicMaterial
          color="#aaaaaa"
          transparent
          opacity={0.08}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

// ─── Public SceneCanvas component ────────────────────────────────────────────

interface SceneCanvasProps {
  geometries: GeometryResponse[];
  overlayData?: OverlayData | null;
  vehicleBbox?: { x_min: number; x_max: number; y_min: number; y_max: number; z_min: number; z_max: number } | null;
}

interface BlobEntry {
  geometryId: string;
  url: string;
  parts: string[];
}

export function SceneCanvas({ geometries, overlayData, vehicleBbox }: SceneCanvasProps) {
  const [blobEntries, setBlobEntries] = useState<BlobEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Must be called unconditionally before any early returns
  const { axesGlbUrl, landmarksGlbUrl, overlays, viewerTheme, showOriginAxes, glbLoaded, rhRefVisible, overlaysAllVisible } = useViewerStore();

  const rhRefActive = rhRefVisible && overlaysAllVisible && !!overlayData?.ride_height_ref;

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
        const url = await geometriesApi.getGlbBlobUrl(g.id, g.decimation_ratio ?? 0.05);
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
  }, [readyGeometries.map((g) => g.id).join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

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
      <Canvas
        style={{ width: "100%", height: "100%" }}
        camera={{ position: [15, -15, 8], fov: 45 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={[bgColor]} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 20, 10]} intensity={1.0} />
        <directionalLight position={[-10, -5, -10]} intensity={0.3} />

        <Suspense fallback={null}>
          {blobEntries.map((entry) => (
            <GLBModel key={entry.geometryId} blobUrl={entry.url} parts={entry.parts} rhRefActive={rhRefActive} />
          ))}
          {axesGlbUrl && overlays.wheelAxes && (
            <AxesGLBModel blobUrl={axesGlbUrl} />
          )}
          {landmarksGlbUrl && overlays.landmarks && (
            <LandmarksGLBModel blobUrl={landmarksGlbUrl} />
          )}
          <CameraFitter />
        </Suspense>

        <CameraPresetController />
        <CameraTypeController />
        <FitToPartController />
        <OrbitCenterMarker />
        <PointerEventHandler />

        {showOriginAxes && <OriginAxes vehicleBbox={vehicleBbox} />}

        <OverlayObjects
          overlayData={overlayData}
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
          rotation={[Math.PI / 2, 0, 0]}
        />

        <OrbitControls makeDefault enableDamping={false} />

        <GizmoHelper alignment="bottom-left" margin={[60, 60]}>
          <GizmoViewport
            axisColors={["#ff4444", "#44bb44", "#4499ff"]}
            labelColor="white"
          />
        </GizmoHelper>
      </Canvas>

      {/* Loading overlay — visible while GLB is fetching / parsing */}
      {!glbLoaded && blobEntries.length > 0 && (
        <Center
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            pointerEvents: "none",
          }}
        >
          <Stack align="center" gap="xs">
            <Loader color="white" size="md" />
            <Text c="white" size="sm">Loading 3D model…</Text>
          </Stack>
        </Center>
      )}
    </div>
  );
}
