#!/usr/bin/env python3
# =============================================================================
# PQMS Computation Script — Composite Biomaterial for Wind Energy
# Part of T015 — Phase 2 Foundational
# Reference: contracts/pqms-interface.sql, quality_metrics (D1-D13)
# =============================================================================
"""
PQMS (Product Quality Metric Score) computation and reporting.

Computes per-dimension scores (D1-D13) for any object using the
canonical weight table, stores results in quality_scores table,
and updates the object's aggregate quality_score.

Usage:
    # Compute PQMS for a single object
    python compute_pqms.py --object-id <UUID>

    # List objects needing PQMS computation
    python compute_pqms.py --pending

    # Full report for an object
    python compute_pqms.py --object-id <UUID> --report

    # Verify SC-008 compliance
    python compute_pqms.py --check-sc008
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure project root is on path for direct CLI invocation
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import (
    ObjectNotFound,
    get_object,
)

# Canonical PQMS weights and targets (aligned with pqms_dimension_weights table)
PQMS_DIMENSIONS = [
    {"dimension": "D1_completude",        "weight": 0.12, "target": 9.0},
    {"dimension": "D2_profundidade",      "weight": 0.10, "target": 9.0},
    {"dimension": "D3_rigor",             "weight": 0.15, "target": 9.5},
    {"dimension": "D4_rastreabilidade",   "weight": 0.10, "target": 9.5},
    {"dimension": "D5_conhecimento",      "weight": 0.08, "target": 9.0},
    {"dimension": "D6_integracao",        "weight": 0.08, "target": 9.0},
    {"dimension": "D7_qualidade_numerica","weight": 0.15, "target": 9.5},
    {"dimension": "D8_impacto",           "weight": 0.05, "target": 8.5},
    {"dimension": "D9_vies",             "weight": 0.05, "target": 9.0},
    {"dimension": "D10_ensino",          "weight": 0.05, "target": 9.5},
    {"dimension": "D11_velocidade",      "weight": 0.02, "target": 9.0},
    {"dimension": "D12_satisfacao",      "weight": 0.03, "target": 8.5},
    {"dimension": "D13_inovacao",        "weight": 0.02, "target": 9.0},
]


def compute_pqms(object_id: str, scores: Dict[str, float], evidence: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Compute and store PQMS scores for an object.

    Args:
        object_id: UUID v4 of the object to score.
        scores: Dict mapping dimension name (e.g. 'D1_completude') to score (0-10).
            Must include all 13 dimensions; missing dimensions are scored 0.
        evidence: Optional dict mapping dimension name to evidence string.

    Returns:
        Dict with keys:
            - object_id: the scored object
            - aggregate: weighted PQMS aggregate (0-10)
            - dimensions_stored: count of dimension scores stored
            - dimensions_below_minimum: count below 8.5 minimum
            - pqms_status: 'PASS' if aggregate >= 9.5 and all >= 8.5
            - breakdown: list of per-dimension results

    Raises:
        ObjectNotFound: If object_id does not exist.
        ValueError: If any score is outside 0-10.
    """
    # Validate object exists
    get_object(object_id)  # raises ObjectNotFound if missing

    # Validate all scores
    errors = []
    for d in PQMS_DIMENSIONS:
        dim = d["dimension"]
        score = scores.get(dim, 0)
        if not (0 <= score <= 10):
            errors.append(f"{dim}: score {score} outside valid range [0, 10]")
    if errors:
        raise ValueError("\n".join(errors))

    evidence = evidence or {}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    weighted_sum = 0.0
    total_weight = 0.0
    breakdown = []
    dimensions_below_minimum = 0

    with database() as db:
        for d in PQMS_DIMENSIONS:
            dim = d["dimension"]
            weight = d["weight"]
            target = d["target"]
            score = scores.get(dim, 0)
            ev = evidence.get(dim)

            weighted_sum += score * weight
            total_weight += weight

            below = score < 8.5
            if below:
                dimensions_below_minimum += 1

            breakdown.append({
                "dimension": dim,
                "score": score,
                "weight": weight,
                "target": target,
                "meets_minimum": not below,
                "contribution_pct": round(score * weight * 10, 2),
            })

            # Upsert quality score
            score_id = str(uuid.uuid4())
            db.execute(
                """INSERT INTO quality_scores (id, object_id, dimension, score, weight, evidence, computed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (score_id, object_id, dim, score, weight, json.dumps(ev) if ev else None, now),
            )

        aggregate = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

        # Update object aggregate score (inline to reuse open connection)
        db.execute(
            "UPDATE objects SET quality_score = ?, updated_at = ? WHERE id = ?",
            (aggregate, now, object_id),
        )

        # Determine PASS/FAIL
        if dimensions_below_minimum > 0:
            pqms_status = f"FAIL: {dimensions_below_minimum} dimension(s) below 8.5 minimum"
        elif aggregate >= 9.5:
            pqms_status = "PASS"
        else:
            pqms_status = f"FAIL: aggregate {aggregate} below 9.5"

        db.commit()

    return {
        "object_id": object_id,
        "aggregate": aggregate,
        "dimensions_stored": len(PQMS_DIMENSIONS),
        "dimensions_below_minimum": dimensions_below_minimum,
        "pqms_status": pqms_status,
        "breakdown": breakdown,
    }


def get_pending_objects() -> List[Dict[str, Any]]:
    """List objects needing PQMS computation (never computed or stale).

    Returns:
        List of dicts from v_pqms_pending view.
    """
    with database() as db:
        rows = db.execute("SELECT * FROM v_pqms_pending").fetchall()
    return [dict(r) for r in rows]


def check_sc008() -> Dict[str, Any]:
    """Verify SC-008 compliance across all scored objects.

    Returns:
        Dict with keys:
            - ok: True if SC-008 passes
            - objects_checked: count of objects evaluated
            - objects_passing: count of objects passing SC-008
            - details: list of per-object status
    """
    with database() as db:
        rows = db.execute("SELECT * FROM v_pqms_summary").fetchall()

    details = [dict(r) for r in rows]
    passing = [d for d in details if d["sc008_combined_status"].startswith("PASS")]

    return {
        "ok": len(passing) == len(details) if details else False,
        "objects_checked": len(details),
        "objects_passing": len(passing),
        "details": details,
    }


def print_report(object_id: str) -> None:
    """Print a human-readable PQMS report for an object."""
    try:
        obj = get_object(object_id)
    except ObjectNotFound as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  PQMS Report: {object_id}")
    print(f"  Type: {obj['object_type']}")
    print(f"  Status: {obj['validation_status']}")
    print(f"  Stored Score: {obj['quality_score']}")
    print(f"{'='*60}")

    with database() as db:
        rows = db.execute(
            "SELECT * FROM v_pqms_breakdown WHERE object_id = ? ORDER BY dimension",
            (object_id,),
        ).fetchall()

    if not rows:
        print("  No dimension scores stored. Run compute_pqms() first.")
        return

    print(f"\n  {'Dimension':<22} {'Score':<6} {'Weight':<7} {'Target':<7} {'Status':<8}")
    print(f"  {'-'*50}")
    for r in rows:
        print(f"  {r['dimension']:<22} {r['score']:<6.1f} {r['weight']:<7.2f} {r['target']:<7.1f} {r['dimension_status']:<8}")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PQMS Computation Tool")
    parser.add_argument("--object-id", help="UUID of object to compute PQMS for")
    parser.add_argument("--report", action="store_true", help="Print detailed report")
    parser.add_argument("--pending", action="store_true", help="List objects needing PQMS computation")
    parser.add_argument("--check-sc008", action="store_true", help="Verify SC-008 compliance")
    parser.add_argument("--score", nargs="*", help="Dimension scores as DIM=VAL (e.g. D1_completude=9.0)")
    parser.add_argument("--evidence", nargs="*", help="Evidence strings as DIM=TEXT")

    args = parser.parse_args()

    if args.pending:
        pending = get_pending_objects()
        if pending:
            print(f"Objects needing PQMS computation ({len(pending)}):")
            for p in pending:
                print(f"  {p['object_id']}  [{p['object_type']}]  status={p['computation_status']}")
        else:
            print("All objects have current PQMS scores.")
        return

    if args.check_sc008:
        sc008 = check_sc008()
        print(f"SC-008 Check: {'PASS' if sc008['ok'] else 'FAIL'}")
        print(f"  Objects checked: {sc008['objects_checked']}")
        print(f"  Objects passing: {sc008['objects_passing']}")
        for d in sc008["details"]:
            print(f"  {d['object_id'][:8]}... [{d['object_type']}]: {d['sc008_combined_status']}")
        return

    if args.object_id:
        if args.report:
            print_report(args.object_id)
            return

        if args.score:
            scores = {}
            evidence = {}
            for s in args.score:
                if "=" not in s:
                    print(f"ERROR: score '{s}' must be in DIM=VAL format")
                    sys.exit(1)
                dim, val = s.split("=", 1)
                scores[dim] = float(val)

            if args.evidence:
                for e in args.evidence:
                    if "=" in e:
                        dim, txt = e.split("=", 1)
                        evidence[dim] = txt

            result = compute_pqms(args.object_id, scores, evidence)
            print(f"PQMS computed for {result['object_id']}")
            print(f"  Aggregate: {result['aggregate']}")
            print(f"  Status: {result['pqms_status']}")
        else:
            print_report(args.object_id)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
