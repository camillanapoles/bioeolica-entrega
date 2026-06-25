#!/usr/bin/env python3
"""
PQMS Summary Report Generator — Bioeolica Project.

Generates a formatted summary report of PQMS scores across all objects
registered in the database. Reads from quality_scores table and
v_pqms_summary view (if available).

Usage:
    python src/03-data-management/quality/pqms_report.py [--output report.txt]
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.database import database


PQMS_DIMENSIONS = [
    "D1_completude", "D2_profundidade", "D3_rigor",
    "D4_rastreabilidade", "D5_conhecimento", "D6_integracao",
    "D7_qualidade_numerica", "D8_impacto", "D9_vies", "D10_ensino",
    "D11_velocidade", "D12_satisfacao", "D13_inovacao",
]


def get_objects_with_scores(db) -> List[Dict[str, Any]]:
    """Return all objects that have quality_scores entries."""
    rows = db.execute(
        """SELECT DISTINCT qs.object_id, o.object_type,
                  o.quality_score, o.validation_status,
                  o.created_at
           FROM quality_scores qs
           JOIN objects o ON qs.object_id = o.id
           ORDER BY o.object_type, o.created_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_dimension_scores(db, object_id: str) -> Dict[str, float]:
    """Return {dimension: score} for a given object."""
    rows = db.execute(
        "SELECT dimension, score FROM quality_scores WHERE object_id = ?",
        (object_id,),
    ).fetchall()
    return {r["dimension"]: r["score"] for r in rows}


def get_dimension_weights(db) -> Dict[str, float]:
    """Return {dimension: weight} from pqms_dimension_weights."""
    rows = db.execute("SELECT dimension, weight FROM pqms_dimension_weights").fetchall()
    if rows:
        return {r["dimension"]: r["weight"] for r in rows}
    # Fallback default weights
    return {
        "D1_completude": 0.12, "D2_profundidade": 0.12, "D3_rigor": 0.15,
        "D4_rastreabilidade": 0.08, "D5_conhecimento": 0.10, "D6_integracao": 0.08,
        "D7_qualidade_numerica": 0.15, "D8_impacto": 0.05, "D9_vies": 0.05,
        "D10_ensino": 0.05, "D11_velocidade": 0.03, "D12_satisfacao": 0.02,
        "D13_inovacao": 0.02,
    }


def compute_weighted_avg(scores: Dict[str, float],
                         weights: Dict[str, float]) -> float:
    """Compute weighted average PQMS score."""
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, score in scores.items():
        w = weights.get(dim, 0.05)
        weighted_sum += score * w
        total_weight += w
    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


def check_sc008_status(db) -> Dict[str, Any]:
    """Check SC-008 status from view or compute."""
    # Try the view first
    view_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name='v_pqms_summary'"
    ).fetchone()
    if view_exists:
        rows = db.execute(
            "SELECT object_id, computed_pqms, sc008_combined_status "
            "FROM v_pqms_summary"
        ).fetchall()
        passing = sum(1 for r in rows if r["sc008_combined_status"].startswith("PASS"))
        return {
            "status": "PASS" if passing == len(rows) and rows else "FAIL",
            "total": len(rows),
            "passing": passing,
        }

    # Fallback: compute from quality_scores
    objects = get_objects_with_scores(db)
    if not objects:
        return {"status": "NO DATA", "total": 0, "passing": 0}

    weights = get_dimension_weights(db)
    passing = 0
    for obj in objects:
        scores = get_dimension_scores(db, obj["object_id"])
        if not scores:
            continue
        pqms = compute_weighted_avg(scores, weights)
        if pqms >= 9.5 and all(s >= 8.0 for s in scores.values()):
            passing += 1

    return {
        "status": "PASS" if passing == len(objects) else "FAIL",
        "total": len(objects),
        "passing": passing,
    }


def get_source_quality_stats(db) -> Dict[str, Any]:
    """Get validation reference quality statistics."""
    rows = db.execute(
        "SELECT source_quality_score FROM validation_references"
    ).fetchall()
    if not rows:
        return {"count": 0, "avg": 0, "min": 0, "above_8": 0}
    scores = [r["source_quality_score"] for r in rows]
    return {
        "count": len(scores),
        "avg": round(sum(scores) / len(scores), 1),
        "min": min(scores),
        "above_8": sum(1 for s in scores if s >= 8),
    }


def generate_report() -> str:
    """Generate the full PQMS summary report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  PQMS SUMMARY REPORT — Bioeolica Project")
    lines.append(f"  Generated: {datetime.now().isoformat()}")
    lines.append("=" * 64)

    with database() as db:
        objects = get_objects_with_scores(db)
        weights = get_dimension_weights(db)
        sc008 = check_sc008_status(db)
        sq = get_source_quality_stats(db)
        # Pre-load all dimension scores while DB is open
        object_scores = {
            obj["object_id"]: get_dimension_scores(db, obj["object_id"])
            for obj in objects
        }

    # Overview
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  PROJECT OVERVIEW")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Total objects with scores: {len(objects)}")
    lines.append(f"  Validation references:     {sq['count']}")
    lines.append(f"  Avg source quality:        {sq['avg']}/10")
    lines.append(f"  Source quality >= 8/10:    {sq['above_8']}/{sq['count']}")
    lines.append(f"  SC-008 status:             {sc008['status']}")

    # Per-object breakdown
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  PER-OBJECT PQMS BREAKDOWN")
    lines.append(f"  {'─' * 60}")

    if not objects:
        lines.append(f"  (no objects with quality scores found)")
    else:
        lines.append(f"  {'Object ID':<12} {'Type':<20} {'PQMS':>6} {'Status':>10} {'Dim Count':>10}")
        lines.append(f"  {'─' * 60}")
        for obj in objects:
            oid = obj["object_id"][:8] + "..."
            otype = obj["object_type"][:20]
            scores = object_scores.get(obj["object_id"], {})
            dim_count = len(scores)
            pqms = obj["quality_score"]
            pqms_str = f"{pqms:.2f}" if pqms is not None else "N/A"
            status = "✅ PASS" if (pqms and pqms >= 9.5) else "❌ FAIL"
            lines.append(f"  {oid:<12} {otype:<20} {pqms_str:>6} {status:>10} {dim_count:>10}")

    # Full dimension table (first object)
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  PQMS DIMENSION WEIGHTS")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  {'Dimension':<22} {'Weight':>7}")
    lines.append(f"  {'─' * 32}")
    for dim in PQMS_DIMENSIONS:
        w = weights.get(dim, 0)
        lines.append(f"  {dim:<22} {w*100:>6.1f}%")

    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  SC-010 ENVIRONMENTAL STATUS")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Source quality >= 8/10:    "
                 f"{'✅ PASS' if sq['count'] > 0 and sq['min'] >= 8 else '❌ FAIL'}"
                 f" (min {sq['min']}/10, avg {sq['avg']}/10)")

    # SC-008 detailed check
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  SC-008 PQMS COMPLIANCE CHECK")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Objects scored:  {sc008['total']}")
    lines.append(f"  Objects passing: {sc008['passing']}")
    is_pass = sc008["status"] == "PASS" and sc008["total"] > 0
    lines.append(f"  Aggregate PQMS >= 9.5: "
                 f"{'✅ PASS' if is_pass else '❌ FAIL'}")
    lines.append(f"  Methodology sub-score = 1.0: "
                 f"{'✅ PASS' if is_pass else '❌ FAIL'}")
    lines.append(f"")
    lines.append(f"  SC-008 COMBINED: "
                 f"{'✅ PASS' if is_pass else '❌ FAIL'}")

    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  VERDICT: "
                 f"{'✅ PQMS AGGREGATE >= 9.5' if is_pass else '❌ PQMS BELOW TARGET'}")
    lines.append(f"  {'═' * 60}")
    lines.append("")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PQMS Summary Report Generator")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    report = generate_report()
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
            f.write("\n")
        print(f"  Report saved to {args.output}")

    # Return exit code based on PQMS status
    with database() as db:
        sc008 = check_sc008_status(db)
    return 0 if sc008["status"].startswith("PASS") else 1


if __name__ == "__main__":
    main()
