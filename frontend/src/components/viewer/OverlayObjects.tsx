import * as THREE from "three";
import { useViewerStore } from "../../stores/viewerStore";

interface VehicleBbox {
  x_min: number; x_max: number;
  y_min: number; y_max: number;
  z_min: number; z_max: number;
}

interface OverlayObjectsProps {
  templateSettings?: Record<string, unknown> | null;
  vehicleBbox?: VehicleBbox | null;
}

// ─── Wireframe box helper ────────────────────────────────────────────────────

function WireBox({
  min,
  max,
  color = "white",
  opacity = 1.0,
}: {
  min: [number, number, number];
  max: [number, number, number];
  color?: string;
  opacity?: number;
}) {
  const cx = (min[0] + max[0]) / 2;
  const cy = (min[1] + max[1]) / 2;
  const cz = (min[2] + max[2]) / 2;
  const sx = max[0] - min[0];
  const sy = max[1] - min[1];
  const sz = max[2] - min[2];

  return (
    <mesh position={[cx, cy, cz]}>
      <boxGeometry args={[sx, sy, sz]} />
      <meshBasicMaterial
        color={color}
        wireframe
        transparent={opacity < 1}
        opacity={opacity}
      />
    </mesh>
  );
}

// ─── Ground plane ────────────────────────────────────────────────────────────

function GroundPlane({ z = 0 }: { z: number }) {
  return (
    <mesh position={[0, 0, z]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[100, 100]} />
      <meshBasicMaterial color="#336633" transparent opacity={0.15} side={THREE.DoubleSide} />
    </mesh>
  );
}

// ─── Level-based color for refinement boxes ──────────────────────────────────

const RL_COLORS: Record<number, string> = {
  1: "#aaaaff",
  2: "#8888ff",
  3: "#6666ff",
  4: "#4444ee",
  5: "#2222dd",
  6: "#0000cc",
  7: "#ff4444",
};
function rlColor(level: number): string {
  return RL_COLORS[level] ?? "#ffffff";
}

// ─── Main component ──────────────────────────────────────────────────────────

export function OverlayObjects({ templateSettings, vehicleBbox }: OverlayObjectsProps) {
  const { overlays } = useViewerStore();

  if (!templateSettings || !vehicleBbox) return null;

  const vb = vehicleBbox;
  const vLen = vb.x_max - vb.x_min;
  const vWid = vb.y_max - vb.y_min;
  const vHgt = vb.z_max - vb.z_min;

  const setup = templateSettings.setup as Record<string, unknown> | undefined;
  const setupOption = templateSettings.setup_option as Record<string, unknown> | undefined;

  // ─── Domain box ──────────────────────────────────────────────────────────
  const domainBoxNode = (() => {
    if (!overlays.domainBox || !setup) return null;
    const mults = setup.domain_bounding_box as number[] | undefined;
    if (!Array.isArray(mults) || mults.length < 6) return null;
    const [xm, xp, ym, yp, zm, zp] = mults;
    const domMin: [number, number, number] = [
      vb.x_min + xm * vLen,
      vb.y_min + ym * vWid,
      vb.z_min + zm * vHgt,
    ];
    const domMax: [number, number, number] = [
      vb.x_max + xp * vLen,
      vb.y_max + yp * vWid,
      vb.z_max + zp * vHgt,
    ];
    return <WireBox key="domain" min={domMin} max={domMax} color="#ffffff" opacity={0.6} />;
  })();

  // ─── Refinement boxes ────────────────────────────────────────────────────
  const refinementNodes = (() => {
    if (!overlays.refinementBoxes || !setup) return null;
    const meshing = setup.meshing as Record<string, unknown> | undefined;
    if (!meshing) return null;
    const boxRefinement = meshing.box_refinement as Record<string, { level: number; box: number[] }> | undefined;
    if (!boxRefinement) return null;

    return Object.entries(boxRefinement).map(([name, br]) => {
      const { level, box } = br;
      if (!Array.isArray(box) || box.length < 6) return null;
      const [xm, xp, ym, yp, zm, zp] = box;
      // vehicle_bbox_factors モード: 乗数として扱う
      const bMin: [number, number, number] = [
        vb.x_min + xm * vLen,
        vb.y_min + ym * vWid,
        vb.z_min + zm * vHgt,
      ];
      const bMax: [number, number, number] = [
        vb.x_max + xp * vLen,
        vb.y_max + yp * vWid,
        vb.z_max + zp * vHgt,
      ];
      return (
        <WireBox key={name} min={bMin} max={bMax} color={rlColor(level)} opacity={0.5} />
      );
    });
  })();

  // ─── Ground plane ────────────────────────────────────────────────────────
  const groundNode = (() => {
    if (!overlays.groundPlane) return null;
    return <GroundPlane z={vb.z_min} />;
  })();

  return (
    <>
      {domainBoxNode}
      {refinementNodes}
      {groundNode}
    </>
  );
}
