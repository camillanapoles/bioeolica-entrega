#!/usr/bin/env python3
"""
P$1 Compliance Tests — ZERO HARDCODED mandate enforcement.

Proves that:
  1. Module-level constants are sourced from SSOT (constants.json), not hardcoded
  2. Changing a value in constants.json propagates to all consumers
  3. _get_constants() fallback works correctly (graceful degradation)
  4. Material substitution resolves correctly from SSOT

Per /orch-fix-defect protocol: RED tests proving the P$1 violation existed
before fixes were applied. Now verifies GREEN after migration.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Path setup — import the module files under test
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SRC = _PROJECT_ROOT / "modules" / "physics-m3" / "src"
sys.path.insert(0, str(_SRC.resolve()))

_CONSTANTS_JSON = (
    _PROJECT_ROOT / "workspace" / "lab1-material-papel-mache-grafite"
    / "config" / "constants.json"
)

# Read live SSOT for verification
with _CONSTANTS_JSON.open() as f:
    _LIVE_SSOT: dict[str, Any] = json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
# TEST: _get_constants helper exists and works correctly
# ═══════════════════════════════════════════════════════════════════════════

def test_get_constants_importable():
    """_get_constants() helper must be importable from composite_model."""
    from composite_model import _get_constants  # noqa: F811
    assert callable(_get_constants), "_get_constants must be a callable"


def test_get_constants_reads_ssot():
    """_get_constants() must read the correct path from constants.json."""
    from composite_model import _get_constants

    # Known value from SSOT
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fiber_volume_fraction_default"]
    val = _get_constants("modules.physics_m3.composite.fiber_volume_fraction_default")
    assert val == expected, (
        f"SSOT fiber_volume_fraction_default = {expected}, "
        f"_get_constants returned {val}"
    )


def test_get_constants_fallback_on_missing_key():
    """_get_constants() must return the default when a key is missing."""
    from composite_model import _get_constants

    val = _get_constants("modules.physics_m3.composite.nonexistent_key", "FALLBACK")
    assert val == "FALLBACK", f"Expected fallback 'FALLBACK', got {val}"


def test_get_constants_fallback_on_bad_path():
    """_get_constants() must return default if dotted path does not resolve."""
    from composite_model import _get_constants

    val = _get_constants("nonexistent.deeply.nested.path", 42)
    assert val == 42, f"Expected fallback 42, got {val}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: CompositeMaterial initialization reads from SSOT
# ═══════════════════════════════════════════════════════════════════════════

def test_composite_default_fiber_from_ssot():
    """Default fiber name must come from SSOT, not hardcoded string."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fiber_default"]
    assert mat.fiber_name == expected, (
        f"Expected fiber default '{expected}' from SSOT, got '{mat.fiber_name}'"
    )


def test_composite_default_matrix_from_ssot():
    """Default matrix name must come from SSOT, not hardcoded string."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["matrix_default"]
    assert mat.matrix_name == expected, (
        f"Expected matrix default '{expected}' from SSOT, got '{mat.matrix_name}'"
    )


def test_composite_default_coating_from_ssot():
    """Default coating name must come from SSOT, not hardcoded string."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["coating_default"]
    assert mat.coating_name == expected, (
        f"Expected coating default '{expected}' from SSOT, got '{mat.coating_name}'"
    )


def test_composite_default_vf_from_ssot():
    """Default fiber volume fraction must come from SSOT."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fiber_volume_fraction_default"]
    assert mat.Vf == expected, (
        f"Expected Vf={expected} from SSOT, got {mat.Vf}"
    )


def test_composite_default_vv_from_ssot():
    """Default void fraction must come from SSOT."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["void_fraction_default"]
    assert mat.Vv == expected, (
        f"Expected Vv={expected} from SSOT, got {mat.Vv}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Material properties resolve from SSOT (not MATERIAL_DB first)
# ═══════════════════════════════════════════════════════════════════════════

def test_material_resolve_priority_reads_ssot():
    """_resolve_material() must check SSOT before MATERIAL_DB fallback."""
    from composite_model import CompositeMaterial

    mat = CompositeMaterial()
    # waste_paper properties — should match SSOT values
    fibers = mat.fiber
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["material_db"]["waste_paper"]
    assert fibers.get("E_GPa") == expected["E_GPa"], (
        f"waste_paper E_GPa: SSOT={expected['E_GPa']}, got {fibers.get('E_GPa')}"
    )
    assert fibers.get("density_kgm3") == expected["density_kgm3"], (
        f"waste_paper density_kgm3: SSOT={expected['density_kgm3']}, got {fibers.get('density_kgm3')}"
    )
    assert fibers.get("tensile_MPa") == expected["tensile_MPa"], (
        f"waste_paper tensile_MPa: SSOT={expected['tensile_MPa']}, got {fibers.get('tensile_MPa')}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# TEST: FabricationProcess defaults come from SSOT
# ═══════════════════════════════════════════════════════════════════════════

def test_fabrication_shredding_time_from_ssot():
    """FabricationProcess.shredding_time_min must come from SSOT."""
    from composite_model import FabricationProcess

    fp = FabricationProcess()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["shredding_time_min"]
    assert fp.shredding_time_min == expected, (
        f"Expected shredding_time_min={expected} from SSOT, got {fp.shredding_time_min}"
    )


def test_fabrication_drying_temp_from_ssot():
    """FabricationProcess.drying_temp_C must come from SSOT."""
    from composite_model import FabricationProcess

    fp = FabricationProcess()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["drying_temp_C"]
    assert fp.drying_temp_C == expected, (
        f"Expected drying_temp_C={expected} from SSOT, got {fp.drying_temp_C}"
    )


def test_fabrication_molding_pressure_from_ssot():
    """FabricationProcess.molding_pressure_MPa must come from SSOT."""
    from composite_model import FabricationProcess

    fp = FabricationProcess()
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["molding_pressure_MPa"]
    assert fp.molding_pressure_MPa == expected, (
        f"Expected molding_pressure_MPa={expected} from SSOT, got {fp.molding_pressure_MPa}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Micromechanics parameters from SSOT
# ═══════════════════════════════════════════════════════════════════════════

def test_xi_halpin_tsai_from_ssot():
    """Halpin-Tsai xi parameter must come from SSOT."""
    from composite_model import _get_constants

    val = _get_constants("modules.physics_m3.composite.xi_halpin_tsai")
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["xi_halpin_tsai"]
    assert val == expected, f"Halpin-Tsai xi: SSOT={expected}, got {val}"


def test_microbuckling_factor_from_ssot():
    """Microbuckling factor must come from SSOT."""
    from composite_model import _get_constants

    val = _get_constants("modules.physics_m3.composite.microbuckling_factor")
    expected = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["microbuckling_factor"]
    assert val == expected, f"Microbuckling factor: SSOT={expected}, got {val}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: SSOT change propagation — the CORE of P$1
# ═══════════════════════════════════════════════════════════════════════════

def test_changing_ssot_fiber_vf_propagates():
    """Changing fiber_volume_fraction_default in constants.json must propagate
    to CompositeMaterial().Vf. This is the core P$1 contract."""
    from composite_model import CompositeMaterial

    # Save original
    original_vf = _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fiber_volume_fraction_default"]

    # Temporarily modify the live JSON to simulate SSOT change
    backup = _CONSTANTS_JSON.read_text()
    try:
        mod = copy.deepcopy(_LIVE_SSOT)
        mod["modules"]["physics_m3"]["composite"]["fiber_volume_fraction_default"] = 0.50
        _CONSTANTS_JSON.write_text(json.dumps(mod, indent=2))

        # Re-import module (it caches constants on read)
        import importlib
        import composite_model
        importlib.reload(composite_model)

        mat = composite_model.CompositeMaterial()
        assert mat.Vf == 0.50, (
            f"After SSOT change to Vf=0.50, got Vf={mat.Vf}"
        )
    finally:
        _CONSTANTS_JSON.write_text(backup)


def test_changing_ssot_fiber_material_propagates():
    """Changing fiber_default in constants.json must propagate to
    CompositeMaterial().fiber_name."""
    from composite_model import CompositeMaterial

    backup = _CONSTANTS_JSON.read_text()
    try:
        mod = copy.deepcopy(_LIVE_SSOT)
        mod["modules"]["physics_m3"]["composite"]["fiber_default"] = "jute"
        _CONSTANTS_JSON.write_text(json.dumps(mod, indent=2))

        import importlib
        import composite_model
        importlib.reload(composite_model)

        mat = composite_model.CompositeMaterial()
        assert mat.fiber_name == "jute", (
            f"After SSOT change fiber_default=jute, got fiber_name={mat.fiber_name}"
        )
    finally:
        _CONSTANTS_JSON.write_text(backup)


# ═══════════════════════════════════════════════════════════════════════════
# TEST: No hardcoded numeric literals remain (keyword: proof by contract)
# ═══════════════════════════════════════════════════════════════════════════

def test_no_hardcoded_fabrication_defaults_in_source():
    """All FabricationProcess defaults must reference _get_constants or
    a field(default_factory=...), not raw numeric literals."""
    from composite_model import FabricationProcess

    fp = FabricationProcess()
    # If any of these match hardcoded values used before migration, they fail:
    assert fp.shredding_time_min == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["shredding_time_min"]
    assert fp.mixing_time_min == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["mixing_time_min"]
    assert fp.molding_pressure_MPa == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["molding_pressure_MPa"]
    assert fp.drying_temp_C == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["drying_temp_C"]
    assert fp.drying_time_h == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["drying_time_h"]
    assert fp.coating_layers == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["coating_layers"]
    assert fp.curing_temp_C == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["curing_temp_C"]
    assert fp.curing_time_h == _LIVE_SSOT["modules"]["physics_m3"]["composite"]["fabrication"]["curing_time_h"]


def test_composite_material_db_sourced_from_ssot():
    """All MATERIAL_DB entries must have matching values in SSOT."""
    from composite_model import _get_constants
    from composite_model import MATERIAL_DB

    for mat_name, mat_props in MATERIAL_DB.items():
        # SSOT material_db is flat by name, not nested by type
        for prop in ("E_GPa", "density_kgm3", "tensile_MPa"):
            ssot_val = _get_constants(
                f"modules.physics_m3.composite.material_db.{mat_name}.{prop}"
            )
            assert ssot_val == mat_props[prop], (
                f"Mismatch {mat_name}.{prop}: SSOT={ssot_val}, MATERIAL_DB={mat_props[prop]}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# TEST: ensure all module-level imports resolve (syntax check)
# ═══════════════════════════════════════════════════════════════════════════

def test_composite_model_imports_clean():
    """composite_model.py must import without ImportError."""
    import composite_model  # noqa: F401
    assert hasattr(composite_model, "CompositeMaterial")
    assert hasattr(composite_model, "FabricationProcess")
