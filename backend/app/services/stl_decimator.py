"""
stl_decimator.py
STL → QEM Decimation → GLB converter
Dependencies: numpy, (optional) tqdm
Usage:
  python stl_decimator.py input.stl output.glb [--ratio 0.2] [--multi] [--verbose]
"""

from __future__ import annotations
import argparse
import heapq
import json
import os
import pathlib
import struct
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np

# ── optional tqdm ─────────────────────────────────────────────
try:
    from tqdm import tqdm as _tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

def _progress(iterable, desc='', total=None):
    if HAS_TQDM:
        return _tqdm(iterable, desc=desc, total=total, ncols=70)
    return iterable

# ── colour palette (SOLID ごとに自動割り当て) ────────────────
PALETTE = [
    [0.29, 0.56, 0.89],  # blue
    [0.49, 0.83, 0.13],  # green
    [0.96, 0.65, 0.14],  # orange
    [0.82, 0.01, 0.11],  # red
    [0.56, 0.07, 0.99],  # purple
    [0.31, 0.89, 0.76],  # cyan
    [0.72, 0.91, 0.53],  # light green
    [0.74, 0.06, 0.88],  # magenta
    [0.29, 0.29, 0.29],  # gray
    [0.97, 0.91, 0.11],  # yellow
]

# ─────────────────────────────────────────────────────────────
# Data container
# ─────────────────────────────────────────────────────────────
@dataclass
class Solid:
    name: str
    verts: np.ndarray   # (N, 3) float64
    faces: np.ndarray   # (M, 3) int32

# ─────────────────────────────────────────────────────────────
# STL Reader
# ─────────────────────────────────────────────────────────────
class STLReader:
    @staticmethod
    def _is_binary(path: pathlib.Path) -> bool:
        with open(path, 'rb') as f:
            header = f.read(80)
            if b'solid' in header[:5].lower():
                # Could be ASCII – verify by comparing declared triangle count
                raw = f.read(4)
                if len(raw) < 4:
                    return False
                n_tris = struct.unpack('<I', raw)[0]
                expected = 84 + n_tris * 50
                actual   = path.stat().st_size
                return abs(expected - actual) <= 4
            return True

    @staticmethod
    def read(path: pathlib.Path, verbose: bool = False) -> list[Solid]:
        if STLReader._is_binary(path):
            if verbose:
                print(f'[STL] Format: Binary')
            return STLReader._read_binary(path, verbose)
        else:
            if verbose:
                print(f'[STL] Format: ASCII')
            return STLReader._read_ascii(path, verbose)

    @staticmethod
    def _read_binary(path: pathlib.Path, verbose: bool) -> list[Solid]:
        with open(path, 'rb') as f:
            f.read(80)  # header
            n_tris = struct.unpack('<I', f.read(4))[0]
            if verbose:
                print(f'[STL] Total triangles: {n_tris:,}')

            verts = np.empty((n_tris * 3, 3), dtype=np.float32)
            for i in _progress(range(n_tris), desc='Reading', total=n_tris) if verbose else range(n_tris):
                f.read(12)  # normal – skip
                for v in range(3):
                    verts[i * 3 + v] = struct.unpack('<fff', f.read(12))
                f.read(2)   # attribute

        faces = np.arange(n_tris * 3, dtype=np.int32).reshape(-1, 3)
        return [Solid(name='Model', verts=verts.astype(np.float64), faces=faces)]

    @staticmethod
    def _read_ascii(path: pathlib.Path, verbose: bool) -> list[Solid]:
        solids: list[Solid] = []
        name   = 'Part_1'
        verts_list: list[list[float]] = []
        faces_list: list[list[int]]   = []
        vi = 0

        with open(path, 'r', errors='replace') as f:
            for line in f:
                s = line.strip()
                sl = s.lower()
                if sl.startswith('solid'):
                    candidate = s[5:].strip()
                    name = candidate if candidate else f'Part_{len(solids) + 1}'
                    verts_list, faces_list, vi = [], [], 0
                elif sl.startswith('vertex '):
                    parts = sl.split()
                    verts_list.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    vi += 1
                elif sl == 'endfacet':
                    if vi >= 3:
                        base = len(verts_list) - vi
                        faces_list.append([base + vi - 3, base + vi - 2, base + vi - 1])
                elif sl.startswith('endsolid'):
                    if faces_list:
                        solids.append(Solid(
                            name=name,
                            verts=np.array(verts_list, dtype=np.float64),
                            faces=np.array(faces_list, dtype=np.int32),
                        ))
                    verts_list, faces_list, vi = [], [], 0

        # Handle file without closing 'endsolid'
        if faces_list:
            solids.append(Solid(
                name=name,
                verts=np.array(verts_list, dtype=np.float64),
                faces=np.array(faces_list, dtype=np.int32),
            ))

        if verbose:
            total = sum(len(s.faces) for s in solids)
            print(f'[STL] Total triangles: {total:,}  ({len(solids)} SOLID)')
        return solids


# ─────────────────────────────────────────────────────────────
# QEM Decimator
# ─────────────────────────────────────────────────────────────
class QEMDecimator:
    """
    Quadric Error Metrics mesh simplification.
    Input:  non-indexed (STL-style) vertex array + face index array
    Output: simplified verts + faces (non-indexed, flat-shading ready)
    """

    @staticmethod
    def _merge_vertices(verts: np.ndarray, faces: np.ndarray):
        """Deduplicate vertices to produce proper shared-vertex mesh."""
        # Round to reduce floating point noise before dedup
        rounded = np.round(verts, decimals=6)
        # Use structured array trick for unique rows
        dt = np.dtype((np.void, rounded.dtype.itemsize * 3))
        view = np.ascontiguousarray(rounded).view(dt).ravel()
        _, inv, counts = np.unique(view, return_inverse=True, return_counts=True)
        unique_verts = verts[np.unique(inv[np.argsort(inv)], return_index=True)[1]]
        # Rebuild unique verts in original order
        order = np.argsort(inv, kind='stable')
        seen: dict[int, int] = {}
        remap = np.empty(len(verts), dtype=np.int32)
        uid = 0
        for orig_idx, uniq_idx in zip(range(len(verts)), inv):
            if uniq_idx not in seen:
                seen[uniq_idx] = uid
                uid += 1
            remap[orig_idx] = seen[uniq_idx]

        new_verts_list = [None] * uid
        for orig_idx in range(len(verts)):
            new_verts_list[remap[orig_idx]] = verts[orig_idx]
        new_verts = np.array(new_verts_list, dtype=np.float64)
        new_faces = remap[faces]
        # Remove degenerate faces
        valid = (new_faces[:, 0] != new_faces[:, 1]) & \
                (new_faces[:, 1] != new_faces[:, 2]) & \
                (new_faces[:, 0] != new_faces[:, 2])
        return new_verts, new_faces[valid]

    @staticmethod
    def _face_quadric(v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        e1 = v1 - v0
        e2 = v2 - v0
        n  = np.cross(e1, e2)
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            return np.zeros((4, 4), dtype=np.float64)
        n /= ln
        d  = -np.dot(n, v0)
        p  = np.array([n[0], n[1], n[2], d], dtype=np.float64)
        return np.outer(p, p)

    @staticmethod
    def _vertex_error(Q: np.ndarray, v: np.ndarray) -> float:
        vh = np.array([v[0], v[1], v[2], 1.0])
        return float(vh @ Q @ vh)

    @staticmethod
    def _optimal_vertex(Q: np.ndarray, v0: np.ndarray, v1: np.ndarray) -> tuple[np.ndarray, float]:
        A = Q[:3, :3]
        b = -Q[:3, 3]
        try:
            det = np.linalg.det(A)
            if abs(det) > 1e-10:
                v_opt = np.linalg.solve(A, b)
                cost  = QEMDecimator._vertex_error(Q, v_opt)
                return v_opt, max(0.0, cost)
        except np.linalg.LinAlgError:
            pass
        # Fallback: test midpoint and both endpoints, pick minimum
        candidates = [v0, v1, (v0 + v1) * 0.5]
        best_v, best_c = min(
            ((c, QEMDecimator._vertex_error(Q, c)) for c in candidates),
            key=lambda x: x[1]
        )
        return best_v, max(0.0, best_c)

    @classmethod
    def simplify(cls, solid: Solid, ratio: float, verbose: bool = False) -> Solid:
        t0 = time.perf_counter()
        n_input = len(solid.faces)
        target  = max(4, int(n_input * ratio))

        if verbose:
            print(f'      Input:  {n_input:>12,} triangles, {len(solid.verts):>12,} vertices')
            print(f'      Target: {target:>12,} triangles ({ratio*100:.1f}%)')

        if ratio >= 1.0 or n_input <= target:
            if verbose:
                print(f'      (Skipped – already at or below target)')
            return solid

        # ── Step 1: merge duplicate vertices ──────────────────
        verts, faces = cls._merge_vertices(solid.verts, solid.faces)
        nv = len(verts)
        nf = len(faces)

        # ── Step 2: per-vertex face membership & quadrics ─────
        # vertex_faces[v] = set of face indices containing v
        vertex_faces: list[set[int]] = [set() for _ in range(nv)]
        Q: list[np.ndarray] = [np.zeros((4, 4), dtype=np.float64) for _ in range(nv)]

        face_verts: list[list[int]] = faces.tolist()   # face_verts[fi] = [v0,v1,v2]
        active:     set[int]        = set(range(nf))   # set of live face indices

        for fi, f in enumerate(face_verts):
            vertex_faces[f[0]].add(fi)
            vertex_faces[f[1]].add(fi)
            vertex_faces[f[2]].add(fi)
            Qf = cls._face_quadric(verts[f[0]], verts[f[1]], verts[f[2]])
            Q[f[0]] += Qf
            Q[f[1]] += Qf
            Q[f[2]] += Qf

        # ── Step 3: collect unique edges ──────────────────────
        edge_set: set[tuple[int, int]] = set()
        for f in face_verts:
            for i in range(3):
                e = (min(f[i], f[(i+1) % 3]), max(f[i], f[(i+1) % 3]))
                edge_set.add(e)

        # ── Step 4: build priority queue ──────────────────────
        heap: list[tuple[float, int, int]] = []
        best_cost: dict[tuple[int, int], float] = {}

        for e in edge_set:
            Qe   = Q[e[0]] + Q[e[1]]
            _, c = cls._optimal_vertex(Qe, verts[e[0]], verts[e[1]])
            best_cost[e] = c
            heapq.heappush(heap, (c, e[0], e[1]))

        # ── Step 5: union-find ────────────────────────────────
        parent = list(range(nv))

        def find(v: int) -> int:
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        # Adjacency for edge-cost recomputation
        adj: list[set[int]] = [set() for _ in range(nv)]
        for e in edge_set:
            adj[e[0]].add(e[1])
            adj[e[1]].add(e[0])

        removed = 0
        target_remove = nf - target
        iter_count    = 0
        report_every  = max(1, target_remove // 20)

        while heap and removed < target_remove:
            cost, a, b = heapq.heappop(heap)
            ra, rb = find(a), find(b)
            if ra == rb:
                continue

            e = (min(ra, rb), max(ra, rb))
            if e not in best_cost or abs(best_cost[e] - cost) > 1e-12:
                continue   # stale

            # ── Contract rb → ra ──────────────────────────
            Qe        = Q[ra] + Q[rb]
            v_opt, _  = cls._optimal_vertex(Qe, verts[ra], verts[rb])
            verts[ra] = v_opt
            Q[ra]     = Qe
            parent[rb] = ra

            # ── Update only faces incident to rb ──────────
            for fi in list(vertex_faces[rb]):
                if fi not in active:
                    vertex_faces[rb].discard(fi)
                    continue
                f = face_verts[fi]
                # Replace rb with ra in this face
                new_f = [ra if v == rb else v for v in f]
                face_verts[fi] = new_f

                # Check for degenerate (collapsed) face
                if len(set(new_f)) < 3:
                    active.discard(fi)
                    for v in f:
                        rv = find(v)
                        vertex_faces[rv].discard(fi)
                    removed += 1
                else:
                    vertex_faces[ra].add(fi)
                vertex_faces[rb].discard(fi)

            # ── Update adjacency ──────────────────────────
            for nb in list(adj[rb]):
                rnb = find(nb)
                if rnb != ra:
                    adj[ra].add(nb)
                    adj[nb].discard(rb)
                    adj[nb].add(ra)
            adj[ra].discard(rb)
            adj[rb].clear()

            # ── Recompute edge costs for ra's neighbours ──
            for nb in adj[ra]:
                rnb = find(nb)
                if rnb == ra:
                    continue
                ne = (min(ra, rnb), max(ra, rnb))
                Qne  = Q[ra] + Q[rnb]
                _, c = cls._optimal_vertex(Qne, verts[ra], verts[rnb])
                best_cost[ne] = c
                heapq.heappush(heap, (c, ne[0], ne[1]))

            iter_count += 1
            if verbose and iter_count % report_every == 0:
                pct = min(100, int(removed / target_remove * 100))
                bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
                print(f'\r      [{bar}] {pct:3d}%  {removed:,}/{target_remove:,}', end='', flush=True)

        if verbose:
            print()

        # ── Step 6: re-index ──────────────────────────────────
        live_faces = [face_verts[fi] for fi in sorted(active)]
        if not live_faces:
            return Solid(name=solid.name, verts=np.empty((0,3)), faces=np.empty((0,3),dtype=np.int32))

        faces_arr = np.array(live_faces, dtype=np.int32)
        used      = np.unique(faces_arr)
        remap_arr = np.zeros(nv, dtype=np.int32)
        remap_arr[used] = np.arange(len(used), dtype=np.int32)
        new_verts = verts[used]
        new_faces = remap_arr[faces_arr]

        elapsed = time.perf_counter() - t0
        if verbose:
            print(f'      Output: {len(new_faces):>12,} triangles  [{elapsed:.1f}s]')

        return Solid(name=solid.name, verts=new_verts, faces=new_faces)


# ─────────────────────────────────────────────────────────────
# Normal computation
# ─────────────────────────────────────────────────────────────
def compute_normals(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Flat (face) normals, repeated per vertex (flatShading compatible)."""
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    n  = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln < 1e-12] = 1.0
    n /= ln
    # Each triangle has the same normal for all 3 vertices
    normals = np.repeat(n, 3, axis=0)  # (M*3, 3)
    return normals.astype(np.float32)


# ─────────────────────────────────────────────────────────────
# GLB Exporter (pure stdlib – no pygltflib needed)
# ─────────────────────────────────────────────────────────────
class GLBExporter:
    """
    Builds a GLB 2.0 file from a list of Solid objects.
    Each Solid becomes a separate Mesh node in the GLTF scene.
    """

    @staticmethod
    def export(
        solids: list[Solid],
        out_path: pathlib.Path,
        verbose: bool = False,
        colors: "list[tuple[float, float, float, float]] | None" = None,
    ) -> None:
        """Export solids to GLB.

        colors: optional per-solid RGBA float tuples (0–1). Falls back to PALETTE when None
                or when the index is out of range.
        """
        if verbose:
            print(f'[GLB] Exporting {len(solids)} part(s) → {out_path.name}')

        binary_chunks: list[bytes] = []
        buffer_views: list[dict]   = []
        accessors:    list[dict]   = []
        meshes:       list[dict]   = []
        nodes:        list[dict]   = []
        materials:    list[dict]   = []
        byte_offset = 0

        def add_buffer(data: bytes, target: int) -> int:
            """Add binary data, return accessor index."""
            nonlocal byte_offset
            # pad to 4-byte alignment
            pad = (4 - len(data) % 4) % 4
            binary_chunks.append(data + b'\x00' * pad)
            bv_idx = len(buffer_views)
            buffer_views.append({
                'buffer':     0,
                'byteOffset': byte_offset,
                'byteLength': len(data),
                'target':     target,
            })
            byte_offset += len(data) + pad
            return bv_idx

        for i, solid in enumerate(solids):
            # ── Geometry ──────────────────────────────────────
            verts  = solid.verts.astype(np.float32)
            faces  = solid.faces.astype(np.uint32)

            # Non-indexed: expand verts per face for flat shading
            flat_verts = verts[faces.ravel()].astype(np.float32)         # (M*3, 3)
            flat_norms = compute_normals(verts, faces)                    # (M*3, 3)
            flat_idx   = np.arange(len(flat_verts), dtype=np.uint32)     # (M*3,)

            # GLTF ELEMENT_ARRAY_BUFFER = 34963, ARRAY_BUFFER = 34962
            idx_bv    = add_buffer(flat_idx.tobytes(),   34963)
            pos_bv    = add_buffer(flat_verts.tobytes(), 34962)
            norm_bv   = add_buffer(flat_norms.tobytes(), 34962)

            # ── Accessors ─────────────────────────────────────
            n_verts = len(flat_verts)
            pos_min = flat_verts.min(axis=0).tolist()
            pos_max = flat_verts.max(axis=0).tolist()

            idx_acc = len(accessors)
            accessors.append({
                'bufferView':    idx_bv,
                'byteOffset':    0,
                'componentType': 5125,   # UNSIGNED_INT
                'count':         len(flat_idx),
                'type':          'SCALAR',
            })
            pos_acc = len(accessors)
            accessors.append({
                'bufferView':    pos_bv,
                'byteOffset':    0,
                'componentType': 5126,   # FLOAT
                'count':         n_verts,
                'type':          'VEC3',
                'min':           pos_min,
                'max':           pos_max,
            })
            norm_acc = len(accessors)
            accessors.append({
                'bufferView':    norm_bv,
                'byteOffset':    0,
                'componentType': 5126,
                'count':         n_verts,
                'type':          'VEC3',
            })

            # ── Material ──────────────────────────────────────
            if colors and i < len(colors):
                color = list(colors[i])          # caller-supplied RGBA
            else:
                color = PALETTE[i % len(PALETTE)] + [1.0]  # RGBA
            mat_idx = len(materials)
            materials.append({
                'name': f'Material_{i}',
                'pbrMetallicRoughness': {
                    'baseColorFactor': color,
                    'metallicFactor':  0.0,
                    'roughnessFactor': 0.7,
                },
                'doubleSided': True,
            })

            # ── Mesh ──────────────────────────────────────────
            mesh_idx = len(meshes)
            meshes.append({
                'name': solid.name,
                'primitives': [{
                    'attributes': {
                        'POSITION': pos_acc,
                        'NORMAL':   norm_acc,
                    },
                    'indices':  idx_acc,
                    'material': mat_idx,
                    'mode':     4,   # TRIANGLES
                }],
            })
            nodes.append({'mesh': mesh_idx, 'name': solid.name})

        # ── GLTF JSON ─────────────────────────────────────────
        total_bin = byte_offset
        gltf = {
            'asset':   {'version': '2.0', 'generator': 'stl_decimator.py'},
            'scene':   0,
            'scenes':  [{'nodes': list(range(len(nodes)))}],
            'nodes':   nodes,
            'meshes':  meshes,
            'materials': materials,
            'accessors':   accessors,
            'bufferViews': buffer_views,
            'buffers': [{'byteLength': total_bin}],
        }

        json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        # JSON chunk must be padded to 4-byte boundary with spaces
        json_pad   = (4 - len(json_bytes) % 4) % 4
        json_chunk = json_bytes + b' ' * json_pad

        bin_data   = b''.join(binary_chunks)

        # ── GLB header + chunks ───────────────────────────────
        json_chunk_len = len(json_chunk)
        bin_chunk_len  = len(bin_data)
        total_len = 12 + 8 + json_chunk_len + 8 + bin_chunk_len

        with open(out_path, 'wb') as f:
            # Header
            f.write(struct.pack('<III', 0x46546C67, 2, total_len))
            # JSON chunk
            f.write(struct.pack('<II', json_chunk_len, 0x4E4F534A))
            f.write(json_chunk)
            # BIN chunk
            f.write(struct.pack('<II', bin_chunk_len, 0x004E4942))
            f.write(bin_data)

        if verbose:
            size_mb = out_path.stat().st_size / 1024 / 1024
            print(f'[GLB] Done: {out_path.name} ({size_mb:.1f} MB)')


# ─────────────────────────────────────────────────────────────
# Parallel worker (must be top-level for Windows 'spawn' compat)
# ─────────────────────────────────────────────────────────────
def _decimate_worker(args: tuple) -> tuple:
    """Worker for ProcessPoolExecutor: (idx, solid, ratio) -> (idx, result, elapsed)"""
    idx, solid, ratio = args
    t0 = time.perf_counter()
    result = QEMDecimator.simplify(solid, ratio=ratio, verbose=False)
    return idx, result, time.perf_counter() - t0


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def _run(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
    ratio: float,
    verbose: bool,
    workers: int = 1,
) -> None:
    t_total = time.perf_counter()

    if verbose:
        print(f'[STL] Reading: {input_path.name} ({input_path.stat().st_size / 1024**2:.1f} MB)')

    solids = STLReader.read(input_path, verbose=verbose)

    total_in = sum(len(s.faces) for s in solids)
    n = len(solids)
    if verbose:
        print(f'[STL] {n} SOLID(s), {total_in:,} triangles total\n')

    use_parallel = workers > 1 and n > 1
    decimated: list[Solid] = [None] * n  # type: ignore[list-item]

    if use_parallel:
        actual_workers = min(workers, n)
        if verbose:
            print(f'[QEM] Parallel decimation: {actual_workers} workers for {n} parts\n')
        jobs = [(i, s, ratio) for i, s in enumerate(solids)]
        with ProcessPoolExecutor(max_workers=actual_workers) as executor:
            futures = {executor.submit(_decimate_worker, job): job[0] for job in jobs}
            for fut in as_completed(futures):
                idx, result, elapsed = fut.result()
                decimated[idx] = result
                if verbose:
                    print(f'[QEM] Part {idx+1}/{n}: "{solids[idx].name}"  '
                          f'{len(solids[idx].faces):,} -> {len(result.faces):,} tris  [{elapsed:.1f}s]')
    else:
        for idx, solid in enumerate(solids):
            if verbose:
                print(f'[QEM] Part {idx+1}/{n}: "{solid.name}"')
            dec = QEMDecimator.simplify(solid, ratio=ratio, verbose=verbose)
            decimated[idx] = dec
            if verbose:
                print()

    GLBExporter.export(decimated, output_path, verbose=verbose)

    total_out = sum(len(s.faces) for s in decimated)
    elapsed = time.perf_counter() - t_total

    print(f'\n{"="*50}')
    print(f'  Parts:       {len(decimated)}')
    print(f'  Input tris:  {total_in:,}')
    print(f'  Output tris: {total_out:,}  ({total_out/max(1,total_in)*100:.1f}%)')
    print(f'  Output file: {output_path}  ({output_path.stat().st_size/1024**2:.1f} MB)')
    print(f'  Total time:  {elapsed:.1f}s')
    print(f'{"="*50}')


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='stl_decimator',
        description='STL → QEM Decimation → GLB converter (Pure Python + NumPy)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python stl_decimator.py model.stl model_dec.glb
  python stl_decimator.py model.stl model_dec.glb --ratio 0.1
  python stl_decimator.py model.stl model_dec.glb --multi --verbose
  python stl_decimator.py model.stl model_dec.glb --ratio 1.0  # format conversion only
        ''',
    )
    parser.add_argument('input',   type=pathlib.Path, help='Input STL file')
    parser.add_argument('output',  type=pathlib.Path, help='Output GLB file')
    parser.add_argument(
        '--ratio', type=float, default=0.2,
        help='Decimation target ratio 0.05-1.0  (default: 0.2 = keep 20%%)',
    )
    parser.add_argument(
        '--multi', action='store_true',
        help='Generate 3 LOD files: _high(50%%) _mid(20%%) _low(5%%)',
    )
    parser.add_argument(
        '--workers', type=int, default=os.cpu_count() or 1,
        metavar='N',
        help=f'Parallel worker processes (default: {os.cpu_count() or 1} = all CPUs). Use 1 to disable.',
    )
    parser.add_argument('--verbose', '-v', action='store_true', default=True, help='Verbose output (default: on)')

    args = parser.parse_args()

    if not args.input.exists():
        print(f'Error: input file not found: {args.input}', file=sys.stderr)
        sys.exit(1)

    if not args.input.suffix.lower() == '.stl':
        print(f'Warning: expected .stl file, got {args.input.suffix}')

    if not (0.01 <= args.ratio <= 1.0):
        print('Error: --ratio must be between 0.01 and 1.0', file=sys.stderr)
        sys.exit(1)

    if args.multi:
        levels = [('high', 0.5), ('mid', 0.2), ('low', 0.05)]
        stem   = args.output.with_suffix('')
        for label, ratio in levels:
            out = pathlib.Path(f'{stem}_{label}.glb')
            print(f'\n── {label.upper()} ({ratio*100:.0f}%) ──────────────────────')
            _run(args.input, out, ratio=ratio, verbose=args.verbose, workers=args.workers)
    else:
        _run(args.input, args.output, ratio=args.ratio, verbose=args.verbose, workers=args.workers)


if __name__ == '__main__':
    main()
