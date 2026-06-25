#!/usr/bin/env python3
"""
Automated PQMS Computation Pipeline — Composite Biomaterial for Wind Energy.

Reads quality_scores from the database for one or more objects and updates
the aggregate objects.quality_score field. Supports batch processing of
pending or all objects, incremental updates, and SC-008 compliance checks.

This pipeline is the automation layer on top of compute_pqms():
  - compute_pqms() handles single-object scoring with CLI
  - pqms_pipeline handles batch/incremental/SC-008 reporting

Usage:
    from src.03-data-management.quality.pqms_pipeline import run_pipeline

    report = run_pipeline()                        # all pending objects
    report = run_pipeline(object_ids=[...])         # specific objects
    report = run_pipeline(recompute_all=True)       # force recompute all
"""
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database
from src.common.registry import object_exists
from src.common.quality.compute_pqms import (
    PQMS_DIMENSIONS,
    compute_pqms,
    get_pending_objects,
    check_sc008,
)


def _get_objects_with_scores() -> List[Dict[str, Any]]:
    """Get all objects that have at least one quality_scores entry."""
    with database() as db:
        rows = db.execute(
            """SELECT DISTINCT qs.object_id, o.object_type, o.quality_score
               FROM quality_scores qs
               JOIN objects o ON qs.object_id = o.id
               ORDER BY o.object_type"""
        ).fetchall()
    return [dict(r) for r in rows]


def run_pipeline(
    object_ids: Optional[List[str]] = None,
    recompute_all: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run the PQMS computation pipeline.

    Args:
        object_ids: Specific object UUIDs to process (None = auto-detect).
        recompute_all: Force recompute even for objects with current scores.
        verbose: If True, print per-object status during processing.

    Returns:
        Dict with keys:
            - processed: count of objects processed
            - passed: count with PQMS >= 9.5
            - failed_below_minimum: count with dimensions below 8.5
            - failed_aggregate: count with aggregate below 9.5
            - errors: list of error messages
            - sc008: SC-008 compliance check result
            - details: list of per-object results
    """
    start_time = datetime.now(timezone.utc)
    processed = 0
    passed = 0
    failed_below_minimum = 0
    failed_aggregate = 0
    errors = []
    details = []

    # Determine which objects to process
    if object_ids:
        targets = object_ids
    elif recompute_all:
        targets = [r["object_id"] for r in _get_objects_with_scores()]
    else:
        pending = get_pending_objects()
        targets = [p["object_id"] for p in pending]

    if not targets:
        if verbose:
            print("No objects to process.")
        return {
            "processed": 0,
            "passed": 0,
            "failed_below_minimum": 0,
            "failed_aggregate": 0,
            "errors": [],
            "sc008": check_sc008(),
            "details": [],
        }

    for oid in targets:
        if not object_exists(oid):
            errors.append(f"Object '{oid[:8]}...' not found, skipping")
            continue

        # Load quality_scores from DB
        with database() as db:
            rows = db.execute(
                "SELECT dimension, score, evidence FROM quality_scores WHERE object_id = ?",
                (oid,),
            ).fetchall()

        if not rows:
            errors.append(f"Object '{oid[:8]}...' has no quality_scores, skipping")
            continue

        scores = {r["dimension"]: r["score"] for r in rows}
        evidence = {}
        for r in rows:
            if r["evidence"]:
                try:
                    evidence[r["dimension"]] = json.loads(r["evidence"])
                except (json.JSONDecodeError, TypeError):
                    evidence[r["dimension"]] = r["evidence"]

        try:
            result = compute_pqms(oid, scores, evidence)
            processed += 1
            details.append(result)

            if result["pqms_status"] == "PASS":
                passed += 1
            elif "below 8.5" in result["pqms_status"]:
                failed_below_minimum += 1
            else:
                failed_aggregate += 1

            if verbose:
                print(f"  {oid[:8]}... aggregate={result['aggregate']} status={result['pqms_status']}")

        except Exception as e:
            errors.append(f"Object '{oid[:8]}...' error: {e}")
            if verbose:
                print(f"  {oid[:8]}... ERROR: {e}")

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Final SC-008 check
    sc008 = check_sc008()

    report = {
        "processed": processed,
        "passed": passed,
        "failed_below_minimum": failed_below_minimum,
        "failed_aggregate": failed_aggregate,
        "errors": errors,
        "sc008": sc008,
        "details": details,
        "elapsed_seconds": round(elapsed, 2),
    }

    return report


def generate_pqms_summary_report() -> Dict[str, Any]:
    """Generate a consolidated PQMS summary across all objects.

    Returns:
        Dict with aggregate stats, per-object breakdown, and SC-008 status.
    """
    pipeline_report = run_pipeline()

    with database() as db:
        objects_with_scores = db.execute(
            """SELECT o.id, o.object_type, o.quality_score, o.validation_status
               FROM objects o
               WHERE o.quality_score IS NOT NULL
               ORDER BY o.quality_score DESC"""
        ).fetchall()

    scored_objects = [dict(r) for r in objects_with_scores]
    avg_score = (
        sum(o["quality_score"] for o in scored_objects) / len(scored_objects)
        if scored_objects
        else 0.0
    )

    return {
        "pipeline": pipeline_report,
        "scored_objects": len(scored_objects),
        "average_quality_score": round(avg_score, 2),
        "objects": scored_objects,
        "sc008_ok": pipeline_report["sc008"]["ok"],
    }


def main() -> None:
    """CLI entry point for the PQMS pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="PQMS Computation Pipeline")
    parser.add_argument("--all", action="store_true", help="Process all objects with scores")
    parser.add_argument("--pending", action="store_true", help="Process pending objects only (default)")
    parser.add_argument("--object-id", nargs="*", help="Specific object UUIDs to process")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--summary", action="store_true", help="Generate summary report")
    parser.add_argument("--check-sc008", action="store_true", help="Run SC-008 check only")

    args = parser.parse_args()

    if args.check_sc008:
        sc008 = check_sc008()
        print(f"SC-008: {'PASS' if sc008['ok'] else 'FAIL'}")
        print(f"  Objects checked: {sc008['objects_checked']}")
        print(f"  Objects passing: {sc008['objects_passing']}")
        for d in sc008["details"]:
            print(f"  {d['object_id'][:8]}... [{d['object_type']}]: {d['sc008_combined_status']}")
        return

    if args.summary:
        report = generate_pqms_summary_report()
        print(f"PQMS Summary Report")
        print(f"  Pipeline processed: {report['pipeline']['processed']}")
        print(f"  Passed: {report['pipeline']['passed']}")
        print(f"  Failed (below min): {report['pipeline']['failed_below_minimum']}")
        print(f"  Failed (aggregate): {report['pipeline']['failed_aggregate']}")
        print(f"  Scored objects: {report['scored_objects']}")
        print(f"  Average score: {report['average_quality_score']}")
        print(f"  SC-008: {'PASS' if report['sc008_ok'] else 'FAIL'}")
        return

    if args.object_id:
        report = run_pipeline(object_ids=args.object_id, verbose=args.verbose)
    elif args.all:
        report = run_pipeline(recompute_all=True, verbose=args.verbose)
    else:
        report = run_pipeline(verbose=args.verbose)

    print(f"Pipeline complete: {report['processed']} processed")
    print(f"  PASS: {report['passed']}")
    print(f"  FAIL (below minimum): {report['failed_below_minimum']}")
    print(f"  FAIL (aggregate): {report['failed_aggregate']}")
    if report["errors"]:
        print(f"  Errors ({len(report['errors'])}):")
        for e in report["errors"]:
            print(f"    - {e}")


if __name__ == "__main__":
    main()
