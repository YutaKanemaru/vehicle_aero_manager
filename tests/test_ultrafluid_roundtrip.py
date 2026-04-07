"""
Round-trip tests for the Ultrafluid XML ↔ Pydantic pipeline.

Tests parse → serialize → parse produces an identical model.
Covers both Aero and GHN sample files.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from lxml import etree

from app.ultrafluid.parser import parse_ufx
from app.ultrafluid.serializer import serialize_ufx
from app.ultrafluid.schema import UfxSolverDeck

# Paths are relative to the repository root
REPO_ROOT = Path(__file__).parent.parent
AERO_XML = REPO_ROOT / "docs" / "samples" / "aero" / "AUR_v1.2_EXT_1.99_corrected.xml"
GHN_XML = REPO_ROOT / "docs" / "samples" / "GHN" / "CX1_v1.2_GHN_cut_plane_volume_corrected.xml"


def _roundtrip(xml_path: Path) -> tuple[UfxSolverDeck, UfxSolverDeck]:
    """Parse → serialize → parse and return both decks."""
    deck1 = parse_ufx(xml_path)
    xml_bytes = serialize_ufx(deck1)
    deck2 = parse_ufx(io.BytesIO(xml_bytes))  # type: ignore[arg-type]
    return deck1, deck2


# ---------------------------------------------------------------------------
# Aero sample tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not AERO_XML.exists(), reason="Aero sample XML not found")
class TestAeroRoundTrip:
    def test_parse_returns_ufx_solver_deck(self):
        deck = parse_ufx(AERO_XML)
        assert isinstance(deck, UfxSolverDeck)

    def test_version(self):
        deck = parse_ufx(AERO_XML)
        assert deck.version.gui_version != ""
        assert deck.version.solver_version != ""

    def test_simulation_general(self):
        deck = parse_ufx(AERO_XML)
        assert deck.simulation.general.num_coarsest_iterations > 0
        assert deck.simulation.general.mach_factor > 0

    def test_material_positive_values(self):
        deck = parse_ufx(AERO_XML)
        mat = deck.simulation.material
        assert mat.density > 0
        assert mat.dynamic_viscosity > 0
        assert mat.temperature > 0
        assert mat.specific_gas_constant > 0

    def test_aero_has_turbulence(self):
        deck = parse_ufx(AERO_XML)
        assert len(deck.sources.turbulence) > 0

    def test_aero_has_rotating_wheels(self):
        deck = parse_ufx(AERO_XML)
        assert len(deck.meshing.overset.rotating) > 0

    def test_aero_no_section_cut(self):
        deck = parse_ufx(AERO_XML)
        assert deck.output.section_cut == []

    def test_aero_no_transitional_bl_detection(self):
        deck = parse_ufx(AERO_XML)
        assert deck.simulation.wall_modeling.transitional_bl_detection is None

    def test_roundtrip_equality(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1 == deck2

    def test_roundtrip_version(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.version == deck2.version

    def test_roundtrip_simulation(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.simulation == deck2.simulation

    def test_roundtrip_geometry(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.geometry == deck2.geometry

    def test_roundtrip_meshing(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.meshing == deck2.meshing

    def test_roundtrip_boundary_conditions(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.boundary_conditions == deck2.boundary_conditions

    def test_roundtrip_sources(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.sources == deck2.sources

    def test_roundtrip_output(self):
        deck1, deck2 = _roundtrip(AERO_XML)
        assert deck1.output == deck2.output

    def test_serialized_xml_is_valid(self):
        deck = parse_ufx(AERO_XML)
        xml_bytes = serialize_ufx(deck)
        root = etree.fromstring(xml_bytes)
        assert root.tag == "uFX_solver_deck"

    def test_boolean_serialization(self):
        """Booleans must be lowercase 'true'/'false' strings."""
        deck = parse_ufx(AERO_XML)
        xml_bytes = serialize_ufx(deck)
        xml_str = xml_bytes.decode("utf-8")
        assert "True" not in xml_str
        assert "False" not in xml_str


# ---------------------------------------------------------------------------
# GHN sample tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not GHN_XML.exists(), reason="GHN sample XML not found")
class TestGHNRoundTrip:
    def test_parse_returns_ufx_solver_deck(self):
        deck = parse_ufx(GHN_XML)
        assert isinstance(deck, UfxSolverDeck)

    def test_ghn_has_section_cut(self):
        deck = parse_ufx(GHN_XML)
        assert len(deck.output.section_cut) > 0

    def test_ghn_has_transitional_bl_detection(self):
        deck = parse_ufx(GHN_XML)
        assert deck.simulation.wall_modeling.transitional_bl_detection is not None

    def test_ghn_no_turbulence(self):
        deck = parse_ufx(GHN_XML)
        assert deck.sources.turbulence == []

    def test_ghn_no_rotating_wheels(self):
        deck = parse_ufx(GHN_XML)
        assert deck.meshing.overset.rotating == []

    def test_ghn_has_custom_refinement(self):
        deck = parse_ufx(GHN_XML)
        assert len(deck.meshing.refinement.custom) > 0

    def test_roundtrip_equality(self):
        deck1, deck2 = _roundtrip(GHN_XML)
        assert deck1 == deck2

    def test_roundtrip_section_cut(self):
        deck1, deck2 = _roundtrip(GHN_XML)
        assert deck1.output.section_cut == deck2.output.section_cut

    def test_serialized_xml_is_valid(self):
        deck = parse_ufx(GHN_XML)
        xml_bytes = serialize_ufx(deck)
        root = etree.fromstring(xml_bytes)
        assert root.tag == "uFX_solver_deck"

    def test_moment_reference_system_capital_type(self):
        """<Type> must be serialized with capital T."""
        deck = parse_ufx(GHN_XML)
        xml_bytes = serialize_ufx(deck)
        root = etree.fromstring(xml_bytes)
        mrs = root.find("output/moment_reference_system")
        assert mrs is not None
        assert mrs.find("Type") is not None, "<Type> with capital T must be present"


# ---------------------------------------------------------------------------
# Schema validation tests (no file required)
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_wall_model_enum(self):
        from app.ultrafluid.schema import WallModeling
        from pydantic import ValidationError

        wm = WallModeling(wall_model="GLW", coupling="adaptive_two-way")
        assert wm.wall_model == "GLW"

        with pytest.raises(ValidationError):
            WallModeling(wall_model="invalid", coupling="adaptive_two-way")

    def test_parameter_preset_enum(self):
        from app.ultrafluid.schema import SimulationGeneral
        from pydantic import ValidationError

        gen = SimulationGeneral(
            num_coarsest_iterations=100,
            mach_factor=1.0,
            num_ramp_up_iterations=200,
            parameter_preset="default",
        )
        assert gen.parameter_preset == "default"

        with pytest.raises(ValidationError):
            SimulationGeneral(
                num_coarsest_iterations=100,
                mach_factor=1.0,
                num_ramp_up_iterations=200,
                parameter_preset="bad_value",
            )
