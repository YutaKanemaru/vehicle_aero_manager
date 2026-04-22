import * as THREE from "three";
import { useViewerStore } from "../../stores/viewerStore";

// ─── Typed helper ────────────────────────────────────────────────────────────
type AnyRec = Record<string, unknown>;
function asRec(v: unknown): AnyRec | undefined {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as AnyRec) : undefined;
}

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
  const { overlayVisibility } = useViewerStore();
  // Helper: key absent = visible by default
  const vis = (key: string) => overlayVisibility[key] !== false;

  if (!templateSettings || !vehicleBbox) return null;

  const vb = vehicleBbox;
  const vLen = vb.x_max - vb.x_min;
  const vWid = vb.y_max - vb.y_min;
  const vHgt = vb.z_max - vb.z_min;

  const setup = templateSettings.setup as Record<string, unknown> | undefined;
  const setupOption = templateSettings.setup_option as Record<string, unknown> | undefined;
  const simParam = templateSettings.simulation_parameter as Record<string, unknown> | undefined;
  const coarsest = (simParam?.coarsest_voxel_size as number) ?? 0.192;

  // ─── Ground height ────────────────────────────────────────────────────────
  const gc = asRec(asRec(setupOption?.boundary_condition)?.ground);
  const groundMode = gc?.ground_height_mode as string | undefined;
  const groundZ = groundMode === "absolute"
    ? ((gc?.ground_height_absolute as number) ?? 0)
    : vb.z_min + ((gc?.ground_height_offset_from_geom_zMin as number) ?? 0);

  // ─── TG config ────────────────────────────────────────────────────────────
  const tgCfg = asRec(asRec(setupOption?.boundary_condition)?.turbulence_generator);
  const blSuction = asRec(gc?.bl_suction);
  const noSlipXminPos = blSuction?.no_slip_xmin_pos as number | null | undefined;

  // ─── Domain box ──────────────────────────────────────────────────────────
  const domainBoxNode = (() => {
    if (!vis("domain_box") || !setup) return null;
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
    if (!setup) return null;
    const meshing = setup.meshing as Record<string, unknown> | undefined;
    if (!meshing) return null;
    const boxRefinement = meshing.box_refinement as Record<string, { level: number; box: number[] }> | undefined;
    if (!boxRefinement) return null;

    return Object.entries(boxRefinement).map(([name, br]) => {
      if (!vis(`box_${name}`)) return null;
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
    if (!vis("ground_plane")) return null;
    return <GroundPlane z={groundZ} />;
  })();

  // ─── TG ground box ───────────────────────────────────────────────────────
  const tgGroundNode = (() => {
    if (!vis("tg_ground") || !tgCfg?.enable_ground_tg) return null;
    // h_rl6 = coarsest × (0.5^6) × 8 = coarsest / 8
    const h_rl6 = coarsest / 8;
    const xStart = noSlipXminPos ?? vb.x_min;
    const floorY = vWid * 0.85;
    const centerY = (vb.y_min + vb.y_max) / 2;
    const yMin = centerY - floorY / 2;
    const yMax = centerY + floorY / 2;
    return (
      <>
        <WireBox
          min={[xStart, yMin, groundZ]}
          max={[vb.x_max, yMax, groundZ + h_rl6]}
          color="#00ffff"
          opacity={0.7}
        />
        <mesh position={[xStart, centerY, groundZ + h_rl6 / 2]} rotation={[0, Math.PI / 2, 0]}>
          <planeGeometry args={[h_rl6, floorY]} />
          <meshBasicMaterial color="#00ffff" transparent opacity={0.25} side={THREE.DoubleSide} />
        </mesh>
      </>
    );
  })();

  // ─── TG body box ─────────────────────────────────────────────────────────
  const tgBodyNode = (() => {
    if (!vis("tg_body") || !tgCfg?.enable_body_tg) return null;
    const tgX = vb.x_min - vLen * 0.05;
    const carYCenter = (vb.y_min + vb.y_max) / 2;
    const yMin = carYCenter - vWid * 0.45;
    const yMax = carYCenter + vWid * 0.45;
    const zMin = vb.z_min + vHgt * 0.10;
    const zMax = vb.z_min + vHgt * 0.65;
    const boxH = zMax - zMin;
    const boxW = yMax - yMin;
    return (
      <>
        <WireBox
          min={[tgX, yMin, zMin]}
          max={[vb.x_max, yMax, zMax]}
          color="#00ffff"
          opacity={0.7}
        />
        <mesh position={[tgX, carYCenter, zMin + boxH / 2]} rotation={[0, Math.PI / 2, 0]}>
          <planeGeometry args={[boxH, boxW]} />
          <meshBasicMaterial color="#00ffff" transparent opacity={0.25} side={THREE.DoubleSide} />
        </mesh>
      </>
    );
  })();

  // ─── Output settings helper ──────────────────────────────────────────────
  const output = templateSettings.output as Record<string, unknown> | undefined;

  // ─── Probe point spheres ─────────────────────────────────────────────────
  const probeNodes = (() => {
    if (!output) return null;
    const probeFiles = output.probe_files as Array<{
      name: string;
      points: Array<{ x_pos: number; y_pos: number; z_pos: number; description?: string }>;
    }> | undefined;
    if (!probeFiles || probeFiles.length === 0) return null;
    const nodes: JSX.Element[] = [];
    for (const pf of probeFiles) {
      if (!vis(`probe_${pf.name}`)) continue;
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
    if (!output) return null;
    const pvs = output.partial_volumes as Array<{
      name: string;
      bbox_mode?: string;
      bbox?: number[];
      bbox_source_box_name?: string;
    }> | undefined;
    if (!pvs || pvs.length === 0) return null;

    const meshing = setup?.meshing as Record<string, unknown> | undefined;
    const boxRefinement = meshing?.box_refinement as Record<string, { level: number; box: number[] }> | undefined;

    return pvs.map((pv, idx) => {
      if (!vis(`pv_${pv.name}`)) return null;
      let bMin: [number, number, number] | null = null;
      let bMax: [number, number, number] | null = null;

      if (pv.bbox_mode === "user_defined" && Array.isArray(pv.bbox) && pv.bbox.length >= 6) {
        const [xm, xp, ym, yp, zm, zp] = pv.bbox;
        bMin = [vb.x_min + xm * vLen, vb.y_min + ym * vWid, vb.z_min + zm * vHgt];
        bMax = [vb.x_max + xp * vLen, vb.y_max + yp * vWid, vb.z_max + zp * vHgt];
      } else if (pv.bbox_mode === "from_meshing_box" && pv.bbox_source_box_name && boxRefinement) {
        const br = boxRefinement[pv.bbox_source_box_name];
        if (br && Array.isArray(br.box) && br.box.length >= 6) {
          const [xm, xp, ym, yp, zm, zp] = br.box;
          bMin = [vb.x_min + xm * vLen, vb.y_min + ym * vWid, vb.z_min + zm * vHgt];
          bMax = [vb.x_max + xp * vLen, vb.y_max + yp * vWid, vb.z_max + zp * vHgt];
        }
        // No fallback — unresolved source box = skip
      }
      // around_parts and unknown modes: skip (no 3D approximation)

      if (!bMin || !bMax) return null;
      return <WireBox key={`pv-${idx}`} min={bMin} max={bMax} color="#ff8800" opacity={0.5} />;
    });
  })();

  // ─── Section cuts ────────────────────────────────────────────────────────
  const scNodes = (() => {
    if (!output) return null;
    const scs = output.section_cuts as Array<{
      name: string;
      axis_x: number; axis_y: number; axis_z: number;
      point_x: number; point_y: number; point_z: number;
    }> | undefined;
    if (!scs || scs.length === 0) return null;

    return scs.map((sc, idx) => {
      if (!vis(`sc_${sc.name}`)) return null;
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
      {tgGroundNode}
      {tgBodyNode}
      {probeNodes}
      {pvNodes}
      {scNodes}
    </>
  );
}
