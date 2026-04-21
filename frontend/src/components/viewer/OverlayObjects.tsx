import * as THREE from "three";
import { useViewerStore } from "../../stores/viewerStore";

export interface VehicleBbox {
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

  // ─── Output settings helper ──────────────────────────────────────────────
  const output = templateSettings.output as Record<string, unknown> | undefined;

  // ─── Probe point spheres ─────────────────────────────────────────────────
  const probeNodes = (() => {
    if (!overlays.probeSpheres || !output) return null;
    const probeFiles = output.probe_files as Array<{
      name: string;
      points: Array<{ x_pos: number; y_pos: number; z_pos: number; description?: string }>;
    }> | undefined;
    if (!probeFiles || probeFiles.length === 0) return null;
    const nodes: JSX.Element[] = [];
    for (const pf of probeFiles) {
      for (let i = 0; i < (pf.points ?? []).length; i++) {
        const pt = pf.points[i];
        nodes.push(
          <mesh key={`probe-${pf.name}-${i}`} position={[pt.x_pos, pt.y_pos, pt.z_pos]}>
            <sphereGeometry args={[0.04, 8, 8]} />
            <meshBasicMaterial color="#ffff00" />
          </mesh>
        );
      }
    }
    return nodes;
  })();

  // ─── Partial volume boxes ────────────────────────────────────────────────
  const pvNodes = (() => {
    if (!overlays.partialVolumes || !output) return null;
    const pvs = output.partial_volumes as Array<{
      name: string;
      bbox_mode?: string;
      bbox?: number[];
      bbox_source_box?: string;
    }> | undefined;
    if (!pvs || pvs.length === 0) return null;

    const meshing = setup?.meshing as Record<string, unknown> | undefined;
    const boxRefinement = meshing?.box_refinement as Record<string, { level: number; box: number[] }> | undefined;

    return pvs.map((pv, idx) => {
      let bMin: [number, number, number] | null = null;
      let bMax: [number, number, number] | null = null;

      if (pv.bbox_mode === "user_defined" && Array.isArray(pv.bbox) && pv.bbox.length >= 6) {
        // absolute coordinates
        const [x0, x1, y0, y1, z0, z1] = pv.bbox;
        bMin = [vb.x_min + x0 * vLen, vb.y_min + y0 * vWid, vb.z_min + z0 * vHgt];
        bMax = [vb.x_min + x1 * vLen, vb.y_min + y1 * vWid, vb.z_min + z1 * vHgt];
      } else if (pv.bbox_mode === "from_meshing_box" && pv.bbox_source_box && boxRefinement) {
        const br = boxRefinement[pv.bbox_source_box];
        if (br && Array.isArray(br.box) && br.box.length >= 6) {
          const [xm, xp, ym, yp, zm, zp] = br.box;
          bMin = [vb.x_min + xm * vLen, vb.y_min + ym * vWid, vb.z_min + zm * vHgt];
          bMax = [vb.x_max + xp * vLen, vb.y_max + yp * vWid, vb.z_max + zp * vHgt];
        }
      } else {
        // fallback: show vehicle bbox
        bMin = [vb.x_min, vb.y_min, vb.z_min];
        bMax = [vb.x_max, vb.y_max, vb.z_max];
      }

      if (!bMin || !bMax) return null;
      return <WireBox key={`pv-${idx}`} min={bMin} max={bMax} color="#ff8800" opacity={0.5} />;
    });
  })();

  // ─── Section cuts ────────────────────────────────────────────────────────
  const scNodes = (() => {
    if (!overlays.sectionCuts || !output) return null;
    const scs = output.section_cuts as Array<{
      name: string;
      axis_x: number; axis_y: number; axis_z: number;
      point_x: number; point_y: number; point_z: number;
    }> | undefined;
    if (!scs || scs.length === 0) return null;

    return scs.map((sc, idx) => {
      const normal = new THREE.Vector3(sc.axis_x, sc.axis_y, sc.axis_z).normalize();
      const up = new THREE.Vector3(0, 0, 1);
      const quat = new THREE.Quaternion();
      // Avoid degenerate case where normal == up
      if (Math.abs(normal.dot(up)) > 0.999) {
        quat.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
      } else {
        quat.setFromUnitVectors(up, normal);
      }
      const euler = new THREE.Euler().setFromQuaternion(quat);
      return (
        <mesh
          key={`sc-${idx}`}
          position={[sc.point_x, sc.point_y, sc.point_z]}
          rotation={euler}
        >
          <planeGeometry args={[10, 10]} />
          <meshBasicMaterial color="#ff00ff" transparent opacity={0.2} side={THREE.DoubleSide} />
        </mesh>
      );
    });
  })();

  return (
    <>
      {domainBoxNode}
      {refinementNodes}
      {groundNode}
      {probeNodes}
      {pvNodes}
      {scNodes}
    </>
  );
}
