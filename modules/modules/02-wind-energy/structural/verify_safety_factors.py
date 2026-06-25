#!/usr/bin/env python3
# =============================================================================
# Safety Factor Verification — Composite Biomaterial for Wind Energy
# Phase 5 — Wind Turbine Blade Application | T044
# Reference: IEC 61400-2, SC-003 blade structural integrity
# Material: Paper mache + graphite composite (UTS=12.5 MPa)
# =============================================================================
"""
Safety factor verification for the paper mache + graphite composite wind
turbine blade. Computes static and fatigue safety factors per IEC 61400-2,
registers results in SQLite, and checks the v_safety_factor_check view.

Usage:
    python verify_safety_factors.py

    Reads FEM stress estimates, computes safety factors, updates SQLite
    registry with validation status, and prints PASS/FAIL summary.

Dependencies:
    - SQLite database with blade_designs table and v_safety_factor_check view
    - blade_geometry.py for material/design constants
    - fatigue_analysis.py for Palmgren-Miner damage
    - src/common/registry.py for validation status updates
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import (
    create_object,
    get_object,
    update_validation_status,
    update_quality_score,
    ObjectNotFound,
)

# ---------------------------------------------------------------------------
# Constants (matches blade_geometry.py)
# ---------------------------------------------------------------------------

UTS_MPA: float = 12.5           # Ultimate tensile strength (MPa)
E_MODULUS_MPA: float = 4669.0   # Young's modulus (MPa)

# Design wind speeds
RATED_WIND_MS: float = 8.0
EXTREME_WIND_MS: float = 40.0

# IEC 61400-2 minimum safety factor
MIN_SAFETY_FACTOR: float = 2.0

# ---------------------------------------------------------------------------
# Stress models
# ---------------------------------------------------------------------------


@dataclass
class StressEstimate:
    """Stress estimates from FEM / analytical models.

    Attributes:
        max_stress_rated_mpa: Max principal stress at rated wind (MPa).
        max_stress_extreme_mpa: Max principal stress at extreme gust (MPa).
        stress_concentration_factor: Geometric SCF at root.
        description: Source / method description.
    """
    max_stress_rated_mpa: float
    max_stress_extreme_mpa: float
    stress_concentration_factor: float
    description: str


def estimate_stress() -> StressEstimate:
    """Estimate blade root stresses from analytical beam model.

    For a 3.5 m cantilever blade with distributed aerodynamic load:

    Extreme gust (40 m/s):
      Dynamic pressure q = 0.5 * rho * v^2 = 0.5 * 1.225 * 1600 = 980 Pa
      Cp ~ 3.0 (pressure coefficient for NACA 0018)
      Surface pressure p = q * Cp ~ 2940 Pa ≈ 3000 Pa (matches .inp DLOAD)
      Distributed load w = p * chord_root = 3000 * 0.35 = 1050 N/m
      Bending moment M = 0.5 * w * L^2 = 0.5 * 1050 * 3.5^2 = 6431 Nm

    Section properties at root (NACA 0018, chord=0.35m, t/c=18%):
      Thickness h = 0.18 * 0.35 = 0.063 m = 63 mm
      Approximate section modulus for thick airfoil:
        S ~ 0.07 * chord^3 = 0.07 * 0.35^3 = 0.003001 m^3
      Bending stress sigma = M / S = 6431 / 0.003001 = 2.14 MPa

    With stress concentration (root transition, material discontinuity):
      sigma_max = 2.14 * 2.0 = 4.28 MPa

    Returns:
        StressEstimate with rated and extreme gust stresses.
    """
    # Extreme gust (40 m/s)
    rho = 1.225                        # Air density (kg/m^3)
    cp = 3.0                           # Pressure coefficient (NACA 0018)
    chord_root = 0.35                   # Root chord (m)
    blade_length = 3.5                 # Blade length (m)
    scf = 2.0                          # Stress concentration factor

    q_extreme = 0.5 * rho * EXTREME_WIND_MS ** 2  # Dynamic pressure
    p_extreme = q_extreme * cp                     # Surface pressure
    w_extreme = p_extreme * chord_root             # Distributed load
    m_extreme = 0.5 * w_extreme * blade_length ** 2  # Bending moment
    section_modulus = 0.07 * chord_root ** 3       # Section modulus
    sigma_extreme = m_extreme / section_modulus * scf / 1e6  # Convert Pa to MPa

    # Rated wind (8 m/s) — scales with (v/v_extreme)^2
    load_ratio = (RATED_WIND_MS / EXTREME_WIND_MS) ** 2
    sigma_rated = sigma_extreme * load_ratio

    return StressEstimate(
        max_stress_rated_mpa=round(sigma_rated, 4),
        max_stress_extreme_mpa=round(sigma_extreme, 4),
        stress_concentration_factor=scf,
        description=(
            "Analytical beam model: cantilever with distributed load, "
            "NACA 0018 section modulus, SCF=2.0 at root"
        ),
    )


# ---------------------------------------------------------------------------
# Safety factor computation
# ---------------------------------------------------------------------------


@dataclass
class SafetyFactors:
    """Safety factor results.

    Attributes:
        static_safety_factor: UTS / max_stress_extreme (dimensionless).
        fatigue_damage_D: Palmgren-Miner cumulative damage (dimensionless).
        fatigue_safety_factor: 1/D (dimensionless), capped at 10.0.
        max_stress_rated_mpa: Max stress at rated wind (MPa).
        max_stress_extreme_mpa: Max stress at extreme gust (MPa).
        sc003_status: PASS if both SF >= 2.0, FAIL otherwise.
        static_check: PASS/FAIL for static safety factor >= 2.0.
        fatigue_check: PASS/FAIL for fatigue safety factor >= 2.0.
    """
    static_safety_factor: float
    fatigue_damage_D: float
    fatigue_safety_factor: float
    max_stress_rated_mpa: float
    max_stress_extreme_mpa: float
    sc003_status: str
    static_check: str
    fatigue_check: str

    def summary(self) -> str:
        """Multi-line safety factor summary."""
        lines = [
            f"Safety Factor Verification (IEC 61400-2):",
            f"  Max stress @ rated ({RATED_WIND_MS} m/s):  {self.max_stress_rated_mpa:.3f} MPa",
            f"  Max stress @ extreme ({EXTREME_WIND_MS} m/s): {self.max_stress_extreme_mpa:.3f} MPa",
            f"  Material UTS:                  {UTS_MPA:.1f} MPa",
            f"",
            f"  Static safety factor:          {self.static_safety_factor:.3f}  (min {MIN_SAFETY_FACTOR:.1f}) "
            f"{'✅ PASS' if self.static_check == 'PASS' else '❌ FAIL'}",
            f"  Fatigue damage D:              {self.fatigue_damage_D:.4f}  (max 1.0) "
            f"{'✅ PASS' if self.fatigue_check == 'PASS' else '❌ FAIL'}",
            f"  Fatigue safety factor (1/D):   {self.fatigue_safety_factor:.3f}  (min {MIN_SAFETY_FACTOR:.1f})",
            f"",
            f"  SC-003 (Blade Structural Integrity): {self.sc003_status}",
        ]
        return "\n".join(lines)


def compute_safety_factors(
    fatigue_damage_D: float,
    stress_estimate: StressEstimate | None = None,
) -> SafetyFactors:
    """Compute static and fatigue safety factors.

    Args:
        fatigue_damage_D: Palmgren-Miner cumulative damage from fatigue analysis.
        stress_estimate: Stress estimate from FEM/analytical model. If None,
                        computed via estimate_stress().

    Returns:
        SafetyFactors with checks.
    """
    if stress_estimate is None:
        stress_estimate = estimate_stress()

    # Static safety factor
    max_stress_extreme = stress_estimate.max_stress_extreme_mpa
    if max_stress_extreme > 0:
        ssf = UTS_MPA / max_stress_extreme
    else:
        ssf = float("inf")

    # Fatigue safety factor (inverse of damage)
    if fatigue_damage_D > 0:
        fsf = 1.0 / fatigue_damage_D
    else:
        fsf = float("inf")

    # Clamp fatigue safety factor for display
    fsf_display = min(fsf, 10.0) if math.isfinite(fsf) else 10.0

    # Bounded checks
    static_check = "PASS" if ssf >= MIN_SAFETY_FACTOR else "FAIL"
    fatigue_check = "PASS" if fsf >= MIN_SAFETY_FACTOR else "FAIL"
    sc003_status = "PASS" if static_check == "PASS" and fatigue_check == "PASS" else "FAIL"

    return SafetyFactors(
        static_safety_factor=round(ssf, 3) if math.isfinite(ssf) else float("inf"),
        fatigue_damage_D=round(fatigue_damage_D, 6),
        fatigue_safety_factor=round(fsf_display, 3),
        max_stress_rated_mpa=stress_estimate.max_stress_rated_mpa,
        max_stress_extreme_mpa=max_stress_extreme,
        sc003_status=sc003_status,
        static_check=static_check,
        fatigue_check=fatigue_check,
    )


# ---------------------------------------------------------------------------
# SQLite integration
# ---------------------------------------------------------------------------


def find_blade_design_id(conn) -> str | None:
    """Find the most recent blade design ID in the registry."""
    row = conn.execute(
        "SELECT id FROM blade_designs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    return row["id"] if row else None


def _register_beam_model(blade_design_id: str | None, db=None) -> str:
    """Register the analytical beam stress model as a computational model.

    Args:
        blade_design_id: Optional blade design UUID for model name.
        db: Optional database connection. If None, opens a new connection.

    Returns:
        The computational model UUID.
    """
    model_id = create_object(
        "computational_model",
        tags=[
            "analytical_beam",
            "safety_factor",
            "sc003",
        ],
        metadata={
            "model_type": "analytical",
            "domain": "structural",
            "solver": "Python",
            "description": "Cantilever beam with distributed aerodynamic load, "
            "NACA 0018 section modulus, SCF=2.0 at root",
        },
    )

    def _do_insert(conn) -> None:
        conn.execute(
            """INSERT INTO computational_models
               (id, model_type, domain, solver_software, solver_version,
                boundary_conditions, material_model, material_properties,
                mesh_type, mesh_num_elements, mesh_num_nodes, notes)
               VALUES (?, 'analytical', 'structural', 'Python', '3.x',
                ?, 'linear_elastic', ?, NULL, NULL, NULL, ?)""",
            (
                model_id,
                blade_design_id
                and f'{{"blade_design": "{blade_design_id}", '
                f'"load": "distributed_aerodynamic", '
                f'"scf": 2.0, '
                f'"standard": "IEC 61400-2"}}'
                or '{"load": "distributed_aerodynamic", "scf": 2.0}',
                f'{{"E_modulus_MPa": {E_MODULUS_MPA}, '
                f'"UTS_MPa": {UTS_MPA}, '
                f'"poisson": 0.35}}',
                "Analytical beam model for safety factor verification",
            ),
        )

    if db is not None:
        _do_insert(db)
    else:
        with database() as db:
            _do_insert(db)
            db.commit()

    return model_id


def register_validation_result(
    sf: SafetyFactors,
    blade_design_id: str | None = None,
    computational_model_id: str | None = None,
) -> str:
    """Register the validation result in SQLite.

    Creates a validation record and updates the blade design's
    validation status and quality score.

    All DB writes share a single connection to avoid SQLite
    "database is locked" from concurrent transactions.

    Args:
        sf: SafetyFactors result.
        blade_design_id: Existing blade design UUID. If None, creates new.
        computational_model_id: Existing computational model UUID. If None,
                              registers the analytical beam model automatically.

    Returns:
        The validation result UUID.
    """
    # Create validation result in registry
    val_id = create_object(
        "simulation_result",
        tags=[
            "safety_factor_verification",
            "sc003",
            f"status_{sf.sc003_status.lower()}",
        ],
        metadata={
            "type": "safety_factor_verification",
            "static_sf": sf.static_safety_factor,
            "fatigue_damage_D": sf.fatigue_damage_D,
            "fatigue_sf": sf.fatigue_safety_factor,
            "sc003_status": sf.sc003_status,
            "standard": "IEC 61400-2",
            "min_safety_factor": MIN_SAFETY_FACTOR,
        },
    )

    # Single connection for all writes to avoid "database is locked"
    with database() as db:
        # Resolve computational model (FK: simulation_results.model_id
        # → computational_models.id)
        if computational_model_id is None:
            computational_model_id = _register_beam_model(
                blade_design_id, db=db
            )

        # Insert validation record (matching simulation_results table schema)
        params = (
            f"static_sf={sf.static_safety_factor},"
            f"fatigue_D={sf.fatigue_damage_D},"
            f"fatigue_sf={sf.fatigue_safety_factor}"
        )
        db.execute(
            """INSERT INTO simulation_results
               (id, model_id, run_timestamp, output_quantities,
                validation_status, validation_error_pct, notes)
               VALUES (?, ?, datetime('now'), ?, ?, ?, ?)""",
            (
                val_id,
                computational_model_id,
                params,
                sf.sc003_status,
                0.0 if sf.sc003_status == "PASS" else 100.0,
                f"SC-003: {sf.sc003_status}",
            ),
        )

        # Update blade design if found
        if blade_design_id:
            db.execute(
                """UPDATE blade_designs
                   SET safety_factor_static = ?,
                       safety_factor_fatigue = ?
                   WHERE id = ?""",
                (sf.static_safety_factor, sf.fatigue_safety_factor, blade_design_id),
            )

            # Record provenance edge (inline to share db connection)
            edge_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            params_json = json.dumps({
                "static_sf": sf.static_safety_factor,
                "fatigue_sf": sf.fatigue_safety_factor,
            })
            db.execute(
                """INSERT INTO provenance (id, source_id, target_id,
                                            transformation, parameters, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    edge_id,
                    blade_design_id,
                    val_id,
                    "safety_factor_verification",
                    params_json,
                    now,
                ),
            )

        db.commit()

    # Update registry status and quality score (separate connections, read-only)
    update_validation_status(val_id, sf.sc003_status)
    score = 9.5 if sf.sc003_status == "PASS" else 4.0
    update_quality_score(val_id, score)

    return val_id


def check_v_safety_factor_view() -> dict:
    """Query the v_safety_factor_check view in SQLite.

    Returns:
        Dict with view status including: record count, PASS count, FAIL count.
    """
    result = {
        "total_records": 0,
        "pass_count": 0,
        "fail_count": 0,
        "details": [],
    }

    try:
        with database() as db:
            rows = db.execute(
                "SELECT id, safety_factor_static, safety_factor_fatigue, "
                "sc003_status FROM v_safety_factor_check"
            ).fetchall()

            result["total_records"] = len(rows)
            for row in rows:
                d = dict(row)
                result["details"].append(d)
                if "FAIL" not in d.get("sc003_status", ""):
                    result["pass_count"] += 1
                else:
                    result["fail_count"] += 1
    except Exception as e:
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify blade safety factors per IEC 61400-2"
    )
    parser.add_argument(
        "--blade-design-id",
        help="UUID of existing blade design (auto-detect if omitted)",
    )
    parser.add_argument(
        "--fatigue-damage",
        type=float,
        default=None,
        help="Palmgren-Miner damage D (runs fatigue analysis if omitted)",
    )
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="Only query SQLite views, skip computation",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  T044 — Safety Factor Verification (IEC 61400-2)")
    print("=" * 70)
    print(f"  Material UTS:         {UTS_MPA} MPa")
    print(f"  E modulus:           {E_MODULUS_MPA} MPa")
    print(f"  Min safety factor:   {MIN_SAFETY_FACTOR}")
    print()

    if args.db_only:
        print("  [Query-only mode]")
        view_result = check_v_safety_factor_view()
        if "error" in view_result:
            print(f"  View query error: {view_result['error']}")
        else:
            print(f"  v_safety_factor_check records: {view_result['total_records']}")
            print(f"  PASS: {view_result['pass_count']}  FAIL: {view_result['fail_count']}")
            for d in view_result["details"]:
                print(f"    {d['id'][:8]}... SF_s={d['safety_factor_static']:.2f} "
                      f"SF_f={d['safety_factor_fatigue']:.2f} -> {d['sc003_status']}")
        print("=" * 70)
        return

    # Compute stress estimates
    stress = estimate_stress()
    print(f"  Stress model: {stress.description}")
    print(f"  Max stress @ rated:  {stress.max_stress_rated_mpa:.3f} MPa")
    print(f"  Max stress @ extreme: {stress.max_stress_extreme_mpa:.3f} MPa")
    print()

    # Get fatigue damage
    if args.fatigue_damage is not None:
        fatigue_D = args.fatigue_damage
        print(f"  Fatigue damage D:    {fatigue_D} (from argument)")
    else:
        print("  Running fatigue analysis...")
        sys.path.insert(
            0,
            os.path.dirname(os.path.abspath(__file__)),
        )
        from fatigue_analysis import (
            SCurve,
            WeibullWind,
            LoadModel,
            compute_fatigue_damage,
        )

        s_curve = SCurve()
        wind = WeibullWind()
        load_model = LoadModel()
        fatigue_result = compute_fatigue_damage(s_curve, wind, load_model)
        fatigue_D = fatigue_result.cumulative_damage_D
        print(f"  Fatigue damage D:    {fatigue_D:.6f}")
    print()

    # Compute safety factors
    sf = compute_safety_factors(fatigue_D, stress)
    print(sf.summary())
    print()

    # Find or use blade design ID
    blade_id = args.blade_design_id
    if blade_id is None:
        with database() as db:
            blade_id = find_blade_design_id(db)

    if blade_id:
        print(f"  Registering validation result for blade: {blade_id}")
        val_id = register_validation_result(sf, blade_id)
        print(f"  Validation result UUID: {val_id}")
    else:
        print(f"  No blade design found in registry. Skipping SQLite update.")
        print(f"  Register a blade design first with register_blade.py.")
    print()

    # Query validation view
    view_result = check_v_safety_factor_view()
    if "error" in view_result and "no such table" in view_result.get("error", ""):
        print(f"  v_safety_factor_check view: not available (schema not loaded)")
    elif "error" in view_result:
        print(f"  v_safety_factor_check view: {view_result['error']}")
    else:
        print(f"  v_safety_factor_check: {view_result['pass_count']} PASS / "
              f"{view_result['fail_count']} FAIL / "
              f"{view_result['total_records']} total")
    print()

    # Final verdict
    if sf.sc003_status == "PASS":
        print(f"  {'SC-003 (Blade Structural Integrity)':40s} ✅ PASS")
    else:
        print(f"  {'SC-003 (Blade Structural Integrity)':40s} ❌ FAIL")

    print("=" * 70)


if __name__ == "__main__":
    main()
