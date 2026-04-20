import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Grid, Environment } from "@react-three/drei";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { Center, Text } from "@mantine/core";
import { Loader } from "@mantine/core";
import { geometriesApi, type GeometryResponse } from "../../api/geometries";
import { useViewerStore } from "../../stores/viewerStore";
import { OverlayObjects } from "./OverlayObjects";

// ─── GLB model inner component (rendered inside Suspense) ────────────────────

function GLBModel({
  blobUrl,
  parts,
}: {
  blobUrl: string;
  parts: string[];
}) {
  const { scene } = useGLTF(blobUrl);
  const { partStates, initParts } = useViewerStore();

  // パーツ名でstoreを初期化（1回のみ）
  useEffect(() => {
    if (parts.length > 0) initParts(parts);
  }, [parts.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  // partStates の変化を3Dシーンへ反映
  useEffect(() => {
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
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
      mat.needsUpdate = true;
    });
  }, [scene, partStates]);

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

// ─── Public SceneCanvas component ────────────────────────────────────────────

interface SceneCanvasProps {
  geometries: GeometryResponse[];
  ratio: number;
  templateSettings?: Record<string, unknown> | null;
  vehicleBbox?: Record<string, number> | null;
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

  return (
    <Canvas
      style={{ width: "100%", height: "100%" }}
      camera={{ position: [10, 5, 10], fov: 45 }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 20, 10]} intensity={1.0} />
      <directionalLight position={[-10, -5, -10]} intensity={0.3} />

      <Suspense fallback={null}>
        {blobEntries.map((entry) => (
          <GLBModel key={entry.geometryId} blobUrl={entry.url} parts={entry.parts} />
        ))}
        <CameraFitter blobUrl={blobEntries[0].url} />
      </Suspense>

      <OverlayObjects
        templateSettings={templateSettings}
        vehicleBbox={vehicleBbox}
      />

      <Grid
        args={[100, 100]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#444"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#666"
        fadeDistance={80}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid
      />

      <OrbitControls makeDefault />
    </Canvas>
  );
}
