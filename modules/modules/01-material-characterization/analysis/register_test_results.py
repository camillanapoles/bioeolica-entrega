#!/usr/bin/env python3
"""
T026 — Mechanical Test Result Registration.

Registers mechanical test results for specimens in the bioeolica.db database.
Supports tensile, flexural, compressive, hardness, and fatigue test types
with uncertainty quantification and full provenance linkage.

Usage:
    python src/01-material-characterization/analysis/register_test_results.py

References:
    - quickstart.md section 2.2 for baseline test schema & values
    - contracts/schema-entities.sql for test_results constraint DDL
    - src/common/registry.py for create_object / get_object API
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional

_project_root: str = __file__
for _ in range(4):
    _project_root = _project_root.rpartition("/")[0]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, get_object, ObjectNotFound
from src.common.provenance import record_edge

# ------------------------------------------------------------------
# Test environment defaults (quickstart.md section 2.2)
# ------------------------------------------------------------------

TEST_DATE: str = "2026-06-05"
DEFAULT_OPERATOR: str = "Lab Technician"
DEFAULT_TEMP_C: float = 23.0
DEFAULT_HUMIDITY_PCT: float = 50.0

TEST_RESULT_COLS: list[str] = [
    "id", "specimen_id", "test_standard", "test_type", "property_measured",
    "value", "unit", "uncertainty", "uncertainty_type", "num_replicates",
    "test_date", "testing_machine", "operator", "temperature_c",
    "humidity_pct", "failure_mode", "notes",
]


# ------------------------------------------------------------------
# Core registration function
# ------------------------------------------------------------------

def register_test_result(
    specimen_id: str,
    test_standard: str,
    test_type: str,
    property_measured: str,
    value: float,
    unit: str,
    uncertainty: float,
    uncertainty_type: str,
    num_replicates: int,
    test_date: str = TEST_DATE,
    testing_machine: str = "Instron 5967",
    operator: Optional[str] = DEFAULT_OPERATOR,
    temperature_c: Optional[float] = DEFAULT_TEMP_C,
    humidity_pct: Optional[float] = DEFAULT_HUMIDITY_PCT,
    failure_mode: Optional[str] = None,
    notes: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Register a single mechanical test result.

    Creates an object in the registry (type ``"test_result"``) and inserts
    a row into the ``test_results`` table.

    Args:
        specimen_id: UUID of the tested specimen.
        test_standard: e.g. ``"ASTM D638"``.
        test_type: one of ``tensile``, ``flexural``, ``compressive``,
                   ``hardness``, ``fatigue``, ``impact``.
        property_measured: e.g. ``"tensile_strength"``.
        value: measured numeric value (must be > 0 per schema).
        unit: e.g. ``"MPa"``, ``"GPa"``, ``"Shore D"``.
        uncertainty: measurement uncertainty (>= 0, < value per schema).
        uncertainty_type: ``"standard_deviation"``, ``"confidence_interval"``,
                          or ``"instrument_error"``.
        num_replicates: number of replicate tests (>= 1).
        test_date: ISO 8601 date string.
        testing_machine: equipment identifier.
        operator: operator name or ID.
        temperature_c: ambient temperature during test.
        humidity_pct: ambient relative humidity (0-100).
        failure_mode: e.g. ``"brittle_fracture"``, ``"delamination"``.
        notes: free-text observations.
        **kwargs: any additional keyword arguments are silently accepted
                  (forward-compatibility with future schema columns).

    Returns:
        The UUID v4 string assigned to this test result.
    """
    tags: list[str] = [
        test_type,
        property_measured,
        test_standard.lower().replace(" ", "_"),
    ]

    obj_id: str = create_object(
        "test_result",
        tags=tags,
        metadata={
            "specimen_id": specimen_id,
            "test_standard": test_standard,
            "value": value,
            "unit": unit,
        },
    )

    with database() as db:
        db.execute(
            """INSERT INTO test_results
               (id, specimen_id, test_standard, test_type, property_measured,
                value, unit, uncertainty, uncertainty_type, num_replicates,
                test_date, testing_machine, operator,
                temperature_c, humidity_pct, failure_mode, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj_id,
                specimen_id,
                test_standard,
                test_type,
                property_measured,
                value,
                unit,
                uncertainty,
                uncertainty_type,
                num_replicates,
                test_date,
                testing_machine,
                operator,
                temperature_c,
                humidity_pct,
                failure_mode,
                notes,
            ),
        )
        db.commit()

    # Provenance edge: specimen → test_result (transformation='mechanical_test')
    record_edge(specimen_id, obj_id, "mechanical_test",
                parameters={"test_standard": test_standard, "test_type": test_type})

    return obj_id


# ------------------------------------------------------------------
# Pre-defined test suites (values from quickstart.md section 2.2)
# ------------------------------------------------------------------

COMPOSITE_TESTS: list[dict[str, Any]] = [
    {
        "test_standard": "ASTM D638",
        "test_type": "tensile",
        "property_measured": "tensile_strength",
        "value": 12.5,
        "unit": "MPa",
        "uncertainty": 1.2,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "brittle_fracture",
        "notes": "Composite specimen — graphite-coated. Fracture at mid-span.",
    },
    {
        "test_standard": "ASTM D790",
        "test_type": "flexural",
        "property_measured": "flexural_modulus",
        "value": 3.8,
        "unit": "GPa",
        "uncertainty": 0.4,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "delamination",
        "notes": "Three-point bending. Delamination at compression face.",
    },
    {
        "test_standard": "ASTM D695",
        "test_type": "compressive",
        "property_measured": "compressive_strength",
        "value": 18.0,
        "unit": "MPa",
        "uncertainty": 1.5,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "crushing",
        "notes": "End-loaded compression. Gradual crush failure mode.",
    },
    {
        "test_standard": "ASTM D2240",
        "test_type": "hardness",
        "property_measured": "hardness_shore_d",
        "value": 72.0,
        "unit": "Shore D",
        "uncertainty": 3.0,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Durometer Type D",
        "failure_mode": None,
        "notes": "5 readings across specimen surface. Type D durometer.",
    },
    {
        "test_standard": "ASTM D7774-17",
        "test_type": "fatigue",
        "property_measured": "fatigue_endurance_limit",
        "value": 8.5,
        "unit": "MPa",
        "uncertainty": 0.8,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 3,
        "testing_machine": "Instron E10000",
        "failure_mode": "fatigue_fracture",
        "notes": "Tension-tension, R=0.1, 1e6 cycles endurance limit.",
    },
]

BASELINE_TESTS: list[dict[str, Any]] = [
    {
        "test_standard": "ASTM D638",
        "test_type": "tensile",
        "property_measured": "tensile_strength",
        "value": 10.0,
        "unit": "MPa",
        "uncertainty": 1.0,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "brittle_fracture",
        "notes": "Baseline paper mache — no coating. ~20% lower than composite.",
    },
    {
        "test_standard": "ASTM D790",
        "test_type": "flexural",
        "property_measured": "flexural_modulus",
        "value": 3.1,
        "unit": "GPa",
        "uncertainty": 0.35,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "delamination",
        "notes": "Baseline. ~18% lower flexural modulus than composite.",
    },
    {
        "test_standard": "ASTM D695",
        "test_type": "compressive",
        "property_measured": "compressive_strength",
        "value": 14.0,
        "unit": "MPa",
        "uncertainty": 1.4,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Instron 5967",
        "failure_mode": "crushing",
        "notes": "Baseline. ~22% lower compressive strength than composite.",
    },
    {
        "test_standard": "ASTM D2240",
        "test_type": "hardness",
        "property_measured": "hardness_shore_d",
        "value": 60.0,
        "unit": "Shore D",
        "uncertainty": 3.5,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 5,
        "testing_machine": "Durometer Type D",
        "failure_mode": None,
        "notes": "Baseline. ~17% lower hardness than composite.",
    },
    {
        "test_standard": "ASTM D7774-17",
        "test_type": "fatigue",
        "property_measured": "fatigue_endurance_limit",
        "value": 6.5,
        "unit": "MPa",
        "uncertainty": 0.9,
        "uncertainty_type": "standard_deviation",
        "num_replicates": 3,
        "testing_machine": "Instron E10000",
        "failure_mode": "fatigue_fracture",
        "notes": "Baseline. ~24% lower endurance limit than composite.",
    },
]


def register_composite_results(composite_id: str) -> list[str]:
    """Register all 5 composite test results.

    Args:
        composite_id: UUID of the composite specimen.

    Returns:
        List of 5 test result UUIDs in registration order.
    """
    ids: list[str] = []
    for params in COMPOSITE_TESTS:
        tid = register_test_result(specimen_id=composite_id, **params)
        ids.append(tid)
    return ids


def register_baseline_results(baseline_id: str, composite_id: str) -> list[str]:
    """Register baseline comparison test results.

    Baseline values are ~15-25% lower than composite values to demonstrate
    the mechanical improvement from graphite coating.

    Args:
        baseline_id: UUID of the baseline specimen.

    Returns:
        List of 5 test result UUIDs in registration order.
    """
    ids: list[str] = []
    for params in BASELINE_TESTS:
        tid = register_test_result(specimen_id=baseline_id, **params)
        ids.append(tid)
    return ids


def print_result_summary(specimen_label: str, result_ids: list[str]) -> None:
    """Print a table of test results for a given set of result UUIDs."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    print(f"\n{CYAN}>>> {specimen_label}{RESET}")
    print(
        f"  {'Test':<22} {'Value':>10} {'Unit':<12} "
        f"{'Uncert':>8} {'Repl':>4} {'Std':<14}"
    )
    print(f"  {'-' * 22} {'-' * 10} {'-' * 12} {'-' * 8} {'-' * 4} {'-' * 14}")

    for rid in result_ids:
        with database() as db:
            row = db.execute(
                "SELECT test_type, property_measured, value, unit, "
                "       uncertainty, num_replicates, test_standard "
                "FROM test_results WHERE id = ?",
                (rid,),
            ).fetchone()
        if row:
            d = dict(row)
            prop_short = d["property_measured"][:20]
            print(
                f"  {prop_short:<22} {d['value']:>8.1f}  {d['unit']:<10} "
                f"+-{d['uncertainty']:<4.1f}  {d['num_replicates']:>3}  "
                f"{d['test_standard']:<14}"
            )


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _main() -> None:
    import sys as _sys

    BLUE = "\033[94m"
    RESET = "\033[0m"

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}  TEST RESULT REGISTRATION{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    # --- Accept specimen UUIDs from command line or prompt ---
    if len(_sys.argv) >= 3:
        baseline_id = _sys.argv[1]
        composite_id = _sys.argv[2]
    else:
        print("\n  No UUIDs provided on command line.")
        print("  Usage: python register_test_results.py <baseline_uuid> <composite_uuid>")
        print("  Entering manual UUID input mode.\n")
        baseline_id = input("  Baseline specimen UUID  : ").strip()
        composite_id = input("  Composite specimen UUID : ").strip()

    # Verify both exist in registry
    for label, sid in [("Baseline", baseline_id), ("Composite", composite_id)]:
        try:
            get_object(sid)
            print(f"  [OK] {label} specimen {sid} found in registry.")
        except ObjectNotFound:
            print(f"  [ERROR] {label} specimen {sid} not found. Aborting.")
            _sys.exit(1)

    # Register results
    composite_result_ids: list[str] = register_composite_results(composite_id)
    print(f"\n  Registered {len(composite_result_ids)} composite test results.")

    baseline_result_ids: list[str] = register_baseline_results(baseline_id, composite_id)
    print(f"  Registered {len(baseline_result_ids)} baseline test results.")

    # Print summaries
    print_result_summary("Composite specimen results", composite_result_ids)
    print_result_summary("Baseline specimen results", baseline_result_ids)

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"  Composite result IDs:")
    for rid in composite_result_ids:
        print(f"    {rid}")
    print(f"  Baseline result IDs:")
    for rid in baseline_result_ids:
        print(f"    {rid}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    _main()
