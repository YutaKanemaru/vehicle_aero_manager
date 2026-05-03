import { useMemo, type ReactElement } from "react";
import * as THREE from "three";
import { useViewerStore } from "../../stores/viewerStore";
import type { OverlayData, OverlayAxisItem } from "../../api/preview";

// ─── Props ───────────────────────────────────────────────────────────────────

interface OverlayObjectsProps {
  overlayData?: OverlayData | null;
}

// ─── Wireframe box helper ────────────────────────────────────────────────────

function WireBox({
  min,
  max,
  color = "white",
  opacity = 1.0,
  dimmed = false,
}: {
  min: [number, number, number];
  max: [number, number, number];
  color?: string;
  opacity?: number;
  dimmed?: boolean;
}) {
  const cx = (min[0] + max[0]) / 2;
  const cy = (min[1] + max[1]) / 2;
  const cz = (min[2] + max[2]) / 2;
  const sx = max[0] - min[0];
  const sy = max[1] - min[1];
  const sz = max[2] - min[2];

  const edges = useMemo(() => {
    const box = new THREE.BoxGeometry(sx, sy, sz);
    const eg = new THREE.EdgesGeometry(box);
    box.dispose();
    return eg;
  }, [sx, sy, sz]);

  const fillOpacity  = dimmed ? 0.02 : opacity * 0.12;
  const edgeOpacity  = dimmed ? 0.15 : Math.min(opacity * 0.85, 1);

  return (
    <group position={[cx, cy, cz]}>
      {/* Semi-transparent fill — back-side only to avoid z-fighting */}
      <mesh>
        <boxGeometry args={[sx, sy, sz]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={fillOpacity}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </mesh>
      {/* Outline edges */}
      <lineSegments geometry={edges}>
        <lineBasicMaterial color={color} transparent opacity={edgeOpacity} />
      </lineSegments>
    </group>
  );
}

// ─── Flat rectangle on a floor plane ─────────────────────────────────────────

function FloorRect({
  xMin,
  xMax,
  yMin,
  yMax,
  z,
  color = "#00cc66",
  opacity = 0.3,
  dimmed = false,
}: {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  z: number;
  color?: string;
  opacity?: number;
  dimmed?: boolean;
}) {
  const cx = (xMin + xMax) / 2;
  const cy = (yMin + yMax) / 2;
  const sx = xMax - xMin;
  const sy = yMax - yMin;

  const edges = useMemo(() => {
    const plane = new THREE.PlaneGeometry(sx, sy);
    const eg = new THREE.EdgesGeometry(plane);
    plane.dispose();
    return eg;
  }, [sx, sy]);

  return (
    <group position={[cx, cy, z]}>
      {/* Semi-transparent fill */}
      <mesh>
        <planeGeometry args={[sx, sy]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={dimmed ? 0.04 : opacity}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Wireframe outline */}
      <lineSegments geometry={edges}>
        <lineBasicMaterial color={color} transparent opacity={dimmed ? 0.15 : Math.min(opacity + 0.4, 1)} />
      </lineSegments>
    </group>
  );
}
// ─── Arrow helper for wheel / porous axes ─────────────────────────────────────

function AxisArrow({ item, dimmed }: { item: OverlayAxisItem; dimmed: boolean }) {
  const { shaftGeo, coneGeo, rotation, shaftPos, conePos } = useMemo(() => {
    const dir = new THREE.Vector3(...(item.direction as [number, number, number])).normalize();
    const len = item.length * 2;          // 2× length
    const shaftR = len * 0.03;            // shaft radius (3× the former line-based 0.01)
    const headLen = len * 0.25;
    const headR = shaftR * 3;             // cone base radius (3× shaft)
    const shaftLen = len - headLen;

    // Quaternion to rotate Y-axis cylinder to face `dir`
    const yAxis = new THREE.Vector3(0, 1, 0);
    const quat = new THREE.Quaternion().setFromUnitVectors(yAxis, dir);
    const euler = new THREE.Euler().setFromQuaternion(quat);

    const origin = new THREE.Vector3(...(item.center as [number, number, number]));

    // Shaft extends from (origin - dir*len) to (origin + dir*shaftLen) — bidirectional
    const totalShaftLen = shaftLen + len;
    const shaftCenter = origin.clone().addScaledVector(dir, (shaftLen - len) / 2);
    // Cone center sits at origin + dir * (shaftLen + headLen/2)
    const coneCenter = origin.clone().addScaledVector(dir, shaftLen + headLen / 2);

    return {
      shaftGeo: [shaftR, shaftR, totalShaftLen, 8] as [number, number, number, number],
      coneGeo:  [headR, headLen, 8]                as [number, number, number],
      rotation: euler,
      shaftPos: shaftCenter.toArray() as [number, number, number],
      conePos:  coneCenter.toArray()  as [number, number, number],
    };
  }, [item.direction, item.center, item.length]);

  const color = item.color;
  const opacity = dimmed ? 0.25 : 1.0;

  return (
    <group>
      <mesh position={shaftPos} rotation={rotation}>
        <cylinderGeometry args={shaftGeo} />
        <meshStandardMaterial color={color} transparent={dimmed} opacity={opacity} />
      </mesh>
      <mesh position={conePos} rotation={rotation}>
        <coneGeometry args={coneGeo} />
        <meshStandardMaterial color={color} transparent={dimmed} opacity={opacity} />
      </mesh>
    </group>
  );
}
// ─── Main component ──────────────────────────────────────────────────────────

export function OverlayObjects({ overlayData }: OverlayObjectsProps) {
  const { overlayVisibility, overlaysAllVisible, rhRefVisible } = useViewerStore();
  const vis = (key: string) => overlayVisibility[key] !== false;

  const rhRefActive = rhRefVisible && overlaysAllVisible && !!overlayData?.ride_height_ref;

  if (!overlaysAllVisible || !overlayData) return null;

  const nodes: ReactElement[] = [];

  // ── Domain bounding box ──────────────────────────────────────────────
  if (overlayData.domain_box && vis("domain_box")) {
    const db = overlayData.domain_box;
    nodes.push(
      <WireBox
        key="domain_box"
        min={[db.x_min, db.y_min, db.z_min]}
        max={[db.x_max, db.y_max, db.z_max]}
        color={db.color ?? "#ffffff"}
        opacity={0.6}
        dimmed={rhRefActive}
      />,
    );
  }

  // ── Refinement boxes ─────────────────────────────────────────────────
  for (const rb of overlayData.refinement_boxes) {
    if (!vis(`box_${rb.name}`)) continue;
    nodes.push(
      <WireBox
        key={`ref_${rb.name}`}
        min={[rb.x_min, rb.y_min, rb.z_min]}
        max={[rb.x_max, rb.y_max, rb.z_max]}
        color={rb.color ?? "#aaaaff"}
        opacity={0.5}
        dimmed={rhRefActive}
      />,
    );
  }

  // ── Porous boxes ─────────────────────────────────────────────────────
  for (const pb of overlayData.porous_boxes) {
    if (!vis(`box_${pb.name}`)) continue;
    nodes.push(
      <WireBox
        key={`por_${pb.name}`}
        min={[pb.x_min, pb.y_min, pb.z_min]}
        max={[pb.x_max, pb.y_max, pb.z_max]}
        color={pb.color ?? "#ff4444"}
        opacity={0.6}
        dimmed={rhRefActive}
      />,
    );
  }

  // ── Partial volume boxes ─────────────────────────────────────────────
  for (const pv of overlayData.partial_volume_boxes) {
    if (!vis(`pv_${pv.name}`)) continue;
    nodes.push(
      <WireBox
        key={`pv_${pv.name}`}
        min={[pv.x_min, pv.y_min, pv.z_min]}
        max={[pv.x_max, pv.y_max, pv.z_max]}
        color={pv.color ?? "#ff8800"}
        opacity={0.5}
        dimmed={rhRefActive}
      />,
    );
  }

  // ── Domain part instances (belt patches + uFX_ground) ────────────────
  for (const dp of overlayData.domain_parts) {
    if (!vis(`dp_${dp.name}`)) continue;
    nodes.push(
      <FloorRect
        key={`dp_${dp.name}`}
        xMin={dp.x_min}
        xMax={dp.x_max}
        yMin={dp.y_min}
        yMax={dp.y_max}
        z={dp.z_position}
        color={dp.color ?? "#00cc66"}
        opacity={dp.export_mesh ? 0.3 : 0.2}
        dimmed={rhRefActive}
      />,
    );
  }

  // ── Turbulence generator planes ──────────────────────────────────────
  for (const tg of overlayData.tg_planes) {
    if (!vis(tg.type)) continue;
    const [px, py, pz] = tg.position;
    const [nx, ny, nz] = tg.normal;
    const normal = new THREE.Vector3(nx, ny, nz).normalize();
    const up = new THREE.Vector3(0, 0, 1);
    const quat = new THREE.Quaternion();
    if (Math.abs(normal.dot(up)) > 0.999) {
      quat.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
    } else {
      quat.setFromUnitVectors(up, normal);
    }
    const euler = new THREE.Euler().setFromQuaternion(quat);
    nodes.push(
      <group key={`tg_${tg.name}`}>
        <mesh position={[px, py, pz]} rotation={euler}>
          <planeGeometry args={[tg.height, tg.width]} />
          <meshBasicMaterial
            color={tg.color ?? "#00ffff"}
            transparent
            opacity={rhRefActive ? 0.04 : 0.25}
            side={THREE.DoubleSide}
          />
        </mesh>
        {/* Thin wireframe box for outline visibility */}
        <WireBox
          min={[px, py - tg.width / 2, pz - tg.height / 2]}
          max={[px + 0.001, py + tg.width / 2, pz + tg.height / 2]}
          color={tg.color ?? "#00ffff"}
          opacity={0.9}
          dimmed={rhRefActive}
        />
      </group>,
    );
  }

  // ── Section cuts ─────────────────────────────────────────────────────
  for (const sc of overlayData.section_cut_planes) {
    if (!vis(`sc_${sc.name}`)) continue;
    const [px, py, pz] = sc.position;
    const [nx, ny, nz] = sc.normal;
    const normal = new THREE.Vector3(nx, ny, nz).normalize();
    const upVec = new THREE.Vector3(0, 0, 1);
    const quat = new THREE.Quaternion();
    if (Math.abs(normal.dot(upVec)) > 0.999) {
      quat.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
    } else {
      quat.setFromUnitVectors(upVec, normal);
    }
    const euler = new THREE.Euler().setFromQuaternion(quat);
    nodes.push(
      <mesh key={`sc_${sc.name}`} position={[px, py, pz]} rotation={euler}>
        <planeGeometry args={[sc.width, sc.height]} />
        <meshBasicMaterial
          color={sc.color ?? "#ff00ff"}
          transparent
          opacity={rhRefActive ? 0.03 : 0.2}
          side={THREE.DoubleSide}
        />
      </mesh>,
    );
  }

  // ── Probes ───────────────────────────────────────────────────────────
  for (const probe of overlayData.probes) {
    if (!vis(`probe_${probe.name}`)) continue;
    for (let i = 0; i < probe.points.length; i++) {
      const [x, y, z] = probe.points[i];
      nodes.push(
        <mesh key={`probe_${probe.name}_${i}`} position={[x, y, z]}>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshBasicMaterial color="#ffff00" transparent opacity={rhRefActive ? 0.15 : 1.0} />
        </mesh>,
      );
    }
  }

  // ── Axis arrows (wheel rotation axes + porous flow axes) ──────────────
  for (const ax of overlayData.axes ?? []) {
    if (!vis(`axis_${ax.name}`)) continue;
    nodes.push(
      <AxisArrow key={`axis_${ax.name}`} item={ax} dimmed={rhRefActive} />,
    );
  }

  // ── Ride height reference spheres (front=red, rear=blue) ───────────────
  if (rhRefActive) {
    const rh = overlayData.ride_height_ref!;
    if (rh.reference_z_front != null) {
      nodes.push(
        <mesh
          key="rh_front"
          position={[rh.reference_x_front ?? 0, 0, rh.reference_z_front]}
        >
          <sphereGeometry args={[0.06, 16, 16]} />
          <meshStandardMaterial color="#ff4444" />
        </mesh>,
      );
    }
    if (rh.reference_z_rear != null) {
      nodes.push(
        <mesh
          key="rh_rear"
          position={[rh.reference_x_rear ?? 0, 0, rh.reference_z_rear]}
        >
          <sphereGeometry args={[0.06, 16, 16]} />
          <meshStandardMaterial color="#4444ff" />
        </mesh>,
      );
    }
  }

  return <>{nodes}</>;
}
