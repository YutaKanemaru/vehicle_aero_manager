import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useThree, useFrame } from "@react-three/fiber";
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
  const { partStates, initParts, flatShading, showEdges, selectedPartName } = useViewerStore();

  // パーツ名でstoreを初期化（1回のみ）
  useEffect(() => {
    if (parts.length > 0) initParts(parts);
  }, [parts.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  // flatShading 専用 effect — ON/OFF のたびにマテリアルを再生成して WebGL シェーダーキャッシュをバイパス
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh) || obj.userData?.isEdgeLine) return;
      const old = obj.material instanceof THREE.MeshStandardMaterial
        ? obj.material as THREE.MeshStandardMaterial
        : null;
      const next = new THREE.MeshStandardMaterial({
        flatShading,
        color: old?.color ?? new THREE.Color("#88aabb"),
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

      const state = partStates[obj.name] ?? partStates[obj.parent?.name ?? ""];
      if (!state) {
        mat.needsUpdate = true;
        return;
      }

      obj.visible = state.visible;

      const isSelected = obj.name === selectedPartName || obj.parent?.name === selectedPartName;
      if (isSelected) {
        mat.color.set("#ffff00");
        if (!mat.emissive) mat.emissive = new THREE.Color(0, 0, 0);
        mat.emissive.set("#444400");
      } else {
        mat.color.set(state.color);
        if (mat.emissive) mat.emissive.set("#000000");
      }
      mat.opacity = state.opacity;
      mat.transparent = state.opacity < 1.0;
      mat.needsUpdate = true;
    });
  }, [scene, partStates, selectedPartName]); // eslint-disable-line react-hooks/exhaustive-deps

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
  const { camera, scene: threeScene, controls } = useThree();
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current) return;
    const timer = setTimeout(() => {
      const box = new THREE.Box3().setFromObject(threeScene);
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
      // Z-up: position from +X, -Y, +Z relative to center
      camera.up.set(0, 0, 1);
      camera.position.set(
        center.x + maxDim * 1.0,
        center.y - maxDim * 1.0,
        center.z + maxDim * 0.5,
      );
      camera.lookAt(center);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.target?.copy(center);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (controls as any)?.update?.();
      camera.updateProjectionMatrix();
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
  const { cameraPreset, setCameraPreset } = useViewerStore();
  const { camera, scene: threeScene, controls } = useThree();

  useEffect(() => {
    if (!cameraPreset) return;
    const box = new THREE.Box3().setFromObject(threeScene);
    if (box.isEmpty()) { setCameraPreset(null); return; }
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const dist = Math.max(size.x, size.y, size.z) * 2.0;

    // Z-up: X=forward (downstream), Y=lateral, Z=up
    // front = car nose (low X), rear = car back (high X), side = -Y (driver side)
    const presets: Record<string, THREE.Vector3> = {
      iso:   new THREE.Vector3(center.x + dist, center.y - dist * 0.6, center.z + dist * 0.8),
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
      (camera as THREE.PerspectiveCamera).updateProjectionMatrix?.();
    }
    setCameraPreset(null);
  }, [cameraPreset]); // eslint-disable-line react-hooks/exhaustive-deps

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
  const { fitToTarget, setFitToTarget } = useViewerStore();
  const { camera, controls, invalidate } = useThree();

  useEffect(() => {
    if (!fitToTarget) return;
    const center = new THREE.Vector3(...fitToTarget.center);
    const radius = fitToTarget.radius;
    camera.up.set(0, 0, 1);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const currentTarget = (controls as any)?.target as THREE.Vector3 | undefined;

    if (camera instanceof THREE.OrthographicCamera) {
      // Ortho: keep camera position/direction, adjust zoom so the part fills ~80% of viewport height
      const currentHalfH = (camera.top - camera.bottom) / 2 / Math.max(camera.zoom, 0.001);
      camera.zoom = (currentHalfH / radius) * 0.8;
      // Also move controls target to part center so orbit rotates around it
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
    invalidate();
    setFitToTarget(null);
  }, [fitToTarget]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

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
  ratio: number;
  templateSettings?: Record<string, unknown> | null;
  vehicleBbox?: VehicleBbox | null;
  partInfo?: Record<string, unknown> | null;
}

interface BlobEntry {
  geometryId: string;
  url: string;
  parts: string[];
}

export function SceneCanvas({ geometries, ratio, templateSettings, vehicleBbox, partInfo }: SceneCanvasProps) {
  const [blobEntries, setBlobEntries] = useState<BlobEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Must be called unconditionally before any early returns
  const { axesGlbUrl, landmarksGlbUrl, overlays, viewerTheme, showOriginAxes } = useViewerStore();

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
        <FitToPartController />
        <OrbitCenterMarker />
        <PointerEventHandler />

        {showOriginAxes && <OriginAxes vehicleBbox={vehicleBbox} />}

        <OverlayObjects
          templateSettings={templateSettings}
          vehicleBbox={vehicleBbox}
          partInfo={partInfo}
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
          rotation={[-Math.PI / 2, 0, 0]}
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
