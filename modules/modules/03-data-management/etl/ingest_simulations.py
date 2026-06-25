#!/usr/bin/env python3
"""
Simulation Result ETL Ingestion — Composite Biomaterial for Wind Energy.

Registers simulation results in the universal registry (objects table)
and inserts corresponding records in simulation_results with constraint
validation at the application layer.

Usage:
    from src.03-data-management.etl.ingest_simulations import ingest_simulation

    obj = ingest_simulation(
        model_id="<computational-model-uuid>",
        output_quantities={"stress_max": 45.2, "strain_max": 0.012},
    )
"""
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, object_exists, ValidationError


class SimulationIngestionError(ValueError):
    """Raised on invalid simulation data."""
    pass


VALID_VALIDATION_STATUSES = {"PENDING", "PASS", "FAIL"}


def _validate_simulation_data(data: Dict[str, Any]) -> None:
    """Validate simulation result data against schema constraints."""
    errors = []

    if not data.get("model_id"):
        errors.append("model_id is required")
    elif not object_exists(data["model_id"]):
        errors.append(f"model_id '{data['model_id']}' does not exist")

    if not data.get("output_quantities"):
        errors.append("output_quantities is required")

    # Convergence checks
    cm = data.get("convergence_metric")
    if cm is not None and cm < 0:
        errors.append(f"convergence_metric must be >= 0, got {cm}")

    ct = data.get("convergence_threshold")
    if ct is not None and ct < 0:
        errors.append(f"convergence_threshold must be >= 0, got {ct}")

    mc = data.get("mesh_convergence_pct")
    if mc is not None and mc < 0:
        errors.append(f"mesh_convergence_pct must be >= 0, got {mc}")

    ve = data.get("validation_error_pct")
    if ve is not None and ve < 0:
        errors.append(f"validation_error_pct must be >= 0, got {ve}")

    vs = data.get("validation_status", "PENDING")
    if vs not in VALID_VALIDATION_STATUSES:
        errors.append(f"validation_status must be one of {VALID_VALIDATION_STATUSES}")

    if errors:
        raise SimulationIngestionError("; ".join(errors))


def ingest_simulation(
    model_id: str,
    output_quantities: Dict[str, Any],
    convergence_metric: Optional[float] = None,
    convergence_threshold: Optional[float] = None,
    mesh_convergence_pct: Optional[float] = None,
    output_files: Optional[Dict[str, str]] = None,
    validation_status: str = "PENDING",
    validation_vs_experiment: Optional[str] = None,
    validation_error_pct: Optional[float] = None,
    uncertainty_quantification: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register a simulation result in the universal registry.

    Args:
        model_id: UUID of the computational model used.
        output_quantities: Dict of output quantities (e.g. stress_max, strain_max).
        convergence_metric: Final residual or convergence value.
        convergence_threshold: Target threshold for convergence.
        mesh_convergence_pct: Mesh refinement variation percentage.
        output_files: Dict mapping output type to file paths.
        validation_status: One of PENDING, PASS, FAIL.
        validation_vs_experiment: FK to test_results.id if validated.
        validation_error_pct: Error vs experimental reference.
        uncertainty_quantification: Method used (Monte_Carlo, interval, etc).
        notes: Free-text notes.
        tags: Optional list of search tags.
        metadata: Optional JSON-serializable metadata.

    Returns:
        Dict with 'object_id', 'model_id', and 'status'.

    Raises:
        SimulationIngestionError: On validation failure.
    """
    data = {k: v for k, v in locals().items() if k not in ("tags", "metadata")}
    _validate_simulation_data(data)

    object_id = create_object(
        object_type="simulation_result",
        tags=tags,
        metadata=metadata,
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output_q_json = json.dumps(output_quantities)
    output_f_json = json.dumps(output_files) if output_files else None

    with database() as db:
        db.execute(
            """INSERT INTO simulation_results
               (id, model_id, run_timestamp,
                convergence_metric, convergence_threshold, mesh_convergence_pct,
                output_quantities, output_files,
                validation_status, validation_vs_experiment, validation_error_pct,
                uncertainty_quantification, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                object_id, model_id, now,
                convergence_metric, convergence_threshold, mesh_convergence_pct,
                output_q_json, output_f_json,
                validation_status, validation_vs_experiment, validation_error_pct,
                uncertainty_quantification, notes,
            ),
        )
        db.commit()

    return {
        "object_id": object_id,
        "model_id": model_id,
        "status": "registered",
    }


def list_simulations(
    model_id: Optional[str] = None,
    validation_status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List registered simulation results.

    Args:
        model_id: Optional filter by computational model.
        validation_status: Optional filter by status.

    Returns:
        List of simulation result dicts.
    """
    conditions = ["sr.id = o.id"]
    params = []
    if model_id:
        conditions.append("sr.model_id = ?")
        params.append(model_id)
    if validation_status:
        conditions.append("sr.validation_status = ?")
        params.append(validation_status)

    where = " AND ".join(conditions)
    with database() as db:
        rows = db.execute(
            f"""SELECT o.*, sr.model_id, sr.validation_status as sim_validation_status,
                       sr.convergence_metric, sr.mesh_convergence_pct,
                       sr.validation_error_pct
                FROM simulation_results sr
                JOIN objects o ON {where}
                ORDER BY o.created_at DESC""",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def main() -> None:
    """CLI entry point for simulation ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest simulation result")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output-quantities", required=True, help="JSON dict")
    parser.add_argument("--convergence-metric", type=float)
    parser.add_argument("--convergence-threshold", type=float)
    parser.add_argument("--mesh-convergence-pct", type=float)
    parser.add_argument("--validation-error-pct", type=float)
    parser.add_argument("--notes")
    parser.add_argument("--list", action="store_true", help="List simulation results")

    args = parser.parse_args()

    if args.list:
        sims = list_simulations()
        if sims:
            print(f"Simulation results ({len(sims)}):")
            for s in sims:
                print(f"  {s['id'][:8]}... model={s['model_id'][:8]}... status={s.get('sim_validation_status', 'N/A')}")
        else:
            print("No simulation results registered.")
        return

    output = json.loads(args.output_quantities)

    result = ingest_simulation(
        model_id=args.model_id,
        output_quantities=output,
        convergence_metric=args.convergence_metric,
        convergence_threshold=args.convergence_threshold,
        mesh_convergence_pct=args.mesh_convergence_pct,
        validation_error_pct=args.validation_error_pct,
        notes=args.notes,
    )
    print(f"Simulation result registered: {result['object_id']}")
    print(f"  Model: {result['model_id'][:8]}...")


if __name__ == "__main__":
    main()
