"""
Preview service — generates overlay data for the Template Builder 3D viewer.

Calls ``assemble_ufx_solver_deck()`` with the selected Template + Assembly and
extracts absolute-coordinate overlay primitives from the resulting
``UfxSolverDeck``.  No XML file is created on disk.

The same ``extract_overlay_data()`` function can be reused in the future
Case viewer: parse an already-generated XML → ``UfxSolverDeck`` → overlay.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.models.geometry import GeometryAssembly
from app.models.template import Template
from app.schemas.overlay import (
    OverlayBoxItem,
    OverlayData,
    OverlayDomainPartItem,
    OverlayPartsGroup,
    OverlayPlaneItem,
    OverlayProbeItem,
)
from app.services.compute_engine import (
    _matches_any,
    _matches_pattern,
    assemble_ufx_solver_deck,
)
from app.services.configuration_service import _merge_analysis_results

if TYPE_CHECKING:
    from app.schemas.template_settings import TemplateSettings
    from app.ultrafluid.schema import UfxSolverDeck

logger = logging.getLogger(__name__)

# ─── RL-level colours (matches former frontend RL_COLORS) ───────────────────

RL_COLORS: dict[int, str] = {
    1: "#aaaaff",
    2: "#8888ff",
    3: "#6666ff",
    4: "#4444ee",
    5: "#2222dd",
    6: "#0000cc",
    7: "#ff4444",
}


def _rl_color(level: int) -> str:
    return RL_COLORS.get(level, "#ffffff")


# ─── Core extraction: UfxSolverDeck → OverlayData ────────────────────────────


def extract_overlay_data(
    deck: "UfxSolverDeck",
    template_settings: "TemplateSettings",
    all_part_names: list[str],
) -> OverlayData:
    """Turn a fully-assembled solver deck into viewer overlay primitives.

    Parameters
    ----------
    deck : UfxSolverDeck
        The assembled deck (from ``assemble_ufx_solver_deck`` or ``parse_ufx``).
    template_settings : TemplateSettings
        Original template settings — needed for probe point coordinates
        (the deck only stores the CSV filename) and for Parts-tab pattern
        groups.
    all_part_names : list[str]
        Flat list of part names from the merged analysis result.  Used for
        pattern matching in the Parts tab.
    """

    # ── Domain bounding box ──────────────────────────────────────────────
    dbb = deck.geometry.domain_bounding_box
    domain_box = OverlayBoxItem(
        name="Domain",
        x_min=dbb.x_min, x_max=dbb.x_max,
        y_min=dbb.y_min, y_max=dbb.y_max,
        z_min=dbb.z_min, z_max=dbb.z_max,
        color="#ffffff",
        category="domain",
    )

    # ── Refinement boxes ─────────────────────────────────────────────────
    # We need to distinguish porous boxes from refinement boxes.
    # Porous box names are generated from part_based_box_refinement entries.
    porous_entry_names: set[str] = set()
    pbr_dict = template_settings.setup.meshing.part_based_box_refinement
    per_coeff = template_settings.setup_option.meshing.box_refinement_porous_per_coefficient
    porous_coeffs = template_settings.porous_coefficients
    for entry_name in pbr_dict:
        if per_coeff and porous_coeffs:
            for coeff in porous_coeffs:
                suffix = coeff.part_name.replace("*", "")
                porous_entry_names.add(f"{entry_name}_{suffix}")
        else:
            porous_entry_names.add(entry_name)

    refinement_boxes: list[OverlayBoxItem] = []
    porous_boxes: list[OverlayBoxItem] = []

    for bi in deck.meshing.refinement.box:
        bb = bi.bounding_box
        item = OverlayBoxItem(
            name=bi.name,
            level=bi.refinement_level,
            x_min=bb.x_min, x_max=bb.x_max,
            y_min=bb.y_min, y_max=bb.y_max,
            z_min=bb.z_min, z_max=bb.z_max,
            color=_rl_color(bi.refinement_level),
        )
        if bi.name in porous_entry_names:
            item.category = "porous"
            porous_boxes.append(item)
        else:
            item.category = "refinement"
            refinement_boxes.append(item)

    # ── Partial volume boxes ─────────────────────────────────────────────
    partial_volume_boxes: list[OverlayBoxItem] = []
    for pvi in deck.output.partial_volume:
        bb = pvi.bounding_box
        partial_volume_boxes.append(OverlayBoxItem(
            name=pvi.name,
            x_min=bb.x_min, x_max=bb.x_max,
            y_min=bb.y_min, y_max=bb.y_max,
            z_min=bb.z_min, z_max=bb.z_max,
            color="#ff8800",
            category="partial_volume",
        ))

    # ── Domain part instances (belt patches + uFX_ground) ────────────────
    domain_parts: list[OverlayDomainPartItem] = []
    for dpi in deck.geometry.domain_part.domain_part_instances:
        # Resolve z_position from location + domain bbox
        loc = dpi.location
        if loc == "z_min":
            z_pos = dbb.z_min
        elif loc == "z_max":
            z_pos = dbb.z_max
        elif loc == "x_min":
            z_pos = dbb.x_min
        elif loc == "x_max":
            z_pos = dbb.x_max
        elif loc == "y_min":
            z_pos = dbb.y_min
        elif loc == "y_max":
            z_pos = dbb.y_max
        else:
            z_pos = dbb.z_min

        color = "#00cc66" if dpi.export_mesh else "#ff8800"
        domain_parts.append(OverlayDomainPartItem(
            name=dpi.name,
            location=dpi.location,
            export_mesh=dpi.export_mesh,
            x_min=dpi.bounding_range.x_min,
            x_max=dpi.bounding_range.x_max,
            y_min=dpi.bounding_range.y_min,
            y_max=dpi.bounding_range.y_max,
            z_position=z_pos,
            color=color,
        ))

    # ── Turbulence generator planes ──────────────────────────────────────
    tg_planes: list[OverlayPlaneItem] = []
    for tgi in deck.sources.turbulence:
        tbb = tgi.bounding_box
        x_pos = tgi.point.x_pos
        width = tbb.y_max - tbb.y_min
        height = tbb.z_max - tbb.z_min
        center_y = (tbb.y_min + tbb.y_max) / 2
        center_z = (tbb.z_min + tbb.z_max) / 2
        tg_planes.append(OverlayPlaneItem(
            name=tgi.name,
            type=f"tg_{tgi.name.replace('tg_', '')}",
            position=[x_pos, center_y, center_z],
            normal=[1.0, 0.0, 0.0],     # YZ plane
            width=width,
            height=height,
            color="#00ffff",
        ))

    # ── Section cuts ─────────────────────────────────────────────────────
    section_cut_planes: list[OverlayPlaneItem] = []
    for sci in deck.output.section_cut:
        ax = sci.axis
        pt = sci.point
        section_cut_planes.append(OverlayPlaneItem(
            name=sci.name,
            type="section_cut",
            position=[pt.x_pos, pt.y_pos, pt.z_pos],
            normal=[ax.x_dir, ax.y_dir, ax.z_dir],
            width=10.0,
            height=10.0,
            color="#ff00ff",
        ))

    # ── Probes (from template_settings — the deck only stores CSV name) ──
    probes: list[OverlayProbeItem] = []
    for pf_cfg in template_settings.output.probe_files:
        points = [[pt.x_pos, pt.y_pos, pt.z_pos] for pt in pf_cfg.points]
        probes.append(OverlayProbeItem(
            name=pf_cfg.name,
            points=points,
            radius=pf_cfg.radius or 0.04,
        ))

    # ── Parts groups (pattern badge clusters for the Parts tab) ──────────
    parts_groups: list[OverlayPartsGroup] = []
    tn = template_settings.target_names
    so = template_settings.setup_option
    setup = template_settings.setup

    def _add_group(label: str, patterns: list[str]) -> None:
        if not patterns:
            return
        matched = [p for p in all_part_names if _matches_any(p, patterns)]
        parts_groups.append(OverlayPartsGroup(
            label=label, patterns=patterns, matched_parts=matched,
        ))

    # target_names
    _add_group("Wheel", tn.wheel)
    _add_group("Rim", tn.rim)
    _add_group("Baffle", tn.baffle)
    _add_group("Wind tunnel", tn.windtunnel)

    # Offset refinement parts
    for name, oref in setup.meshing.offset_refinement.items():
        _add_group(f"Offset: {name}", oref.parts)

    # Custom refinement parts
    for name, cref in setup.meshing.custom_refinement.items():
        _add_group(f"Custom: {name}", cref.parts)

    # Ride height reference parts
    _add_group("RH Reference", so.ride_height.reference_parts)

    # Porous coefficients
    for pc in template_settings.porous_coefficients:
        _add_group(f"Porous: {pc.part_name}", [pc.part_name])

    # Triangle splitting instances
    for inst in so.meshing.triangle_splitting_instances:
        _add_group(f"TS: {inst.name}", inst.parts)

    # ── Ground Z ─────────────────────────────────────────────────────────
    ground_z = dbb.z_min

    return OverlayData(
        domain_box=domain_box,
        refinement_boxes=refinement_boxes,
        porous_boxes=porous_boxes,
        partial_volume_boxes=partial_volume_boxes,
        domain_parts=domain_parts,
        tg_planes=tg_planes,
        section_cut_planes=section_cut_planes,
        probes=probes,
        parts_groups=parts_groups,
        ground_z=ground_z,
    )


# ─── Public API: Template + Assembly → OverlayData ───────────────────────────


def compute_overlay_data(
    db: Session,
    template_id: str,
    assembly_id: str,
) -> OverlayData:
    """Assemble a solver deck from Template + Assembly and extract overlay data.

    This endpoint does NOT write any file to disk.
    """
    from app.schemas.template_settings import TemplateSettings

    # 1. Load template + active version
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    active_version = None
    for v in template.versions:
        if v.is_active:
            active_version = v
            break
    if not active_version:
        raise HTTPException(status_code=400, detail="Template has no active version")

    import json
    settings_dict = json.loads(active_version.settings) if isinstance(active_version.settings, str) else active_version.settings
    template_settings = TemplateSettings.model_validate(settings_dict)

    # 2. Load assembly + merge analysis results
    assembly = (
        db.query(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .filter(GeometryAssembly.id == assembly_id)
        .first()
    )
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")

    merged = _merge_analysis_results(assembly)
    all_part_names: list[str] = merged.get("parts", [])

    # 3. Assemble solver deck (no PCA, no disk write)
    try:
        sp = template_settings.simulation_parameter
        deck = assemble_ufx_solver_deck(
            template_settings=template_settings,
            analysis_result=merged,
            sim_type=template.sim_type,
            inflow_velocity=sp.inflow_velocity,
            yaw_angle=sp.yaw_angle,
            source_files=[],         # not needed for overlay
            pca_axes=None,           # skip PCA — overlay doesn't need axes
        )
    except Exception:
        logger.exception("Failed to assemble solver deck for overlay preview")
        raise HTTPException(
            status_code=400,
            detail="Failed to compute overlay. Check template settings and assembly geometry.",
        )

    # 4. Extract overlay data from the assembled deck
    return extract_overlay_data(deck, template_settings, all_part_names)
