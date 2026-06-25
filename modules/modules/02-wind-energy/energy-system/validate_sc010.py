#!/usr/bin/env python3
"""
SC-010 Environmental Validation Runner — Phase 7 US5 Checkpoint.

Runs all LCA scripts, queries the SQLite database for registered results,
and validates every SC-010 target:

  - SC-010-C1: >= 60% lower carbon than fiberglass (blade material)
  - SC-010-C2: >= 80% biodegradable within 5 years (best case)
  - SC-010-C3: Source quality >= 8/10 for all data

Usage:
    python src/02-wind-energy/energy-system/validate_sc010.py
"""

import sys
import os
import json
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.database import database


# ---- SC-010 Targets ---- #

SC010_TARGETS = {
    "carbon_reduction_min_pct": 60.0,
    "biodegradable_min_pct": 80.0,
    "recyclable_min_pct": 80.0,
    "source_quality_min": 8,
}


# ---- Validation result data classes ---- #

@dataclass
class ScriptResult:
    name: str
    path: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass
class SC010Check:
    criterion_id: str
    description: str
    value: float
    target: float
    unit: str
    passed: bool
    source: str  # which script/table produced this


@dataclass
class ValidationReport:
    timestamp: str
    scripts: List[ScriptResult]
    checks: List[SC010Check]
    all_scripts_passed: bool
    all_checks_passed: bool
    summary: str


# ---- Script runner ---- #

SCRIPTS = [
    ("LCA Inventory", "lca_inventory.py"),
    ("Carbon Comparison", "lca_carbon_comparison.py"),
    ("End-of-Life Assessment", "lca_end_of_life.py"),
    ("Comprehensive LCA Report", "lca_report.py"),
    ("Validation References", "ingest_validation_references.py"),
]

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__))
ETL_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "03-data-management", "etl"
)


def run_script(name: str, path: str) -> ScriptResult:
    """Run a Python script and capture output."""
    print(f"  Running {name}...", end=" ")
    sys.stdout.flush()
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=120,
        )
        print(f"exit code {result.returncode}")
        return ScriptResult(
            name=name,
            path=path,
            exit_code=result.returncode,
            stdout=result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
            stderr=result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return ScriptResult(name=name, path=path, exit_code=-1, stdout="", stderr="TIMEOUT")
    except Exception as e:
        print(f"ERROR: {e}")
        return ScriptResult(name=name, path=path, exit_code=-1, stdout="", stderr=str(e))


# ---- Database queries ---- #

def query_simulation_results() -> List[Dict]:
    """Query all simulation_result objects with their output_quantities."""
    results = []
    with database() as db:
        rows = db.execute(
            """SELECT o.id, o.created_at, o.metadata, sr.output_quantities, sr.notes
               FROM objects o
               JOIN simulation_results sr ON sr.id = o.id
               WHERE o.object_type = 'simulation_result'
               ORDER BY o.created_at DESC"""
        ).fetchall()
        for r in rows:
            data = dict(r)
            try:
                data["metadata"] = json.loads(data["metadata"]) if isinstance(data["metadata"], str) else data["metadata"]
            except (json.JSONDecodeError, TypeError):
                pass
            try:
                data["output_quantities"] = json.loads(data["output_quantities"]) if isinstance(data["output_quantities"], str) else data["output_quantities"]
            except (json.JSONDecodeError, TypeError):
                pass
            results.append(data)
    return results


def query_validation_references() -> List[Dict]:
    """Query all validation_reference objects."""
    refs = []
    with database() as db:
        rows = db.execute(
            """SELECT o.id, vr.source_type, vr.title, vr.source_quality_score,
                      vr.validation_metric_type, vr.validation_threshold
               FROM objects o
               JOIN validation_references vr ON vr.id = o.id
               WHERE o.object_type = 'validation_reference'
               ORDER BY vr.source_quality_score DESC"""
        ).fetchall()
        for r in rows:
            refs.append(dict(r))
    return refs


# ---- SC-010 validation ---- #

def extract_carbon_reduction(results: List[Dict]) -> Optional[float]:
    """Extract blade-only carbon reduction % from comparison output.

    Prefers blade_only_carbon_reduction_pct (material comparison excl.
    shared tower/foundation). Falls back to system-level carbon_reduction_pct.
    """
    for r in results:
        meta = r.get("metadata", {})
        if isinstance(meta, dict) and meta.get("type") == "carbon_footprint_comparison":
            oq = r.get("output_quantities", {})
            if isinstance(oq, dict):
                # Prefer blade-only metric (SC-010 target)
                if "blade_only_carbon_reduction_pct" in oq:
                    return oq["blade_only_carbon_reduction_pct"]
                # Fallback to system-level
                if "carbon_reduction_pct" in oq:
                    return oq["carbon_reduction_pct"]
            # Try from the full output quantities
            notes = r.get("notes", "")
            if "SC-010" in notes:
                # Parse from notes
                for part in notes.split(","):
                    if "%" in part:
                        try:
                            return float(part.split("%")[0].split()[-1])
                        except (ValueError, IndexError):
                            pass
    return None


def extract_biodegradable_pct(results: List[Dict]) -> Optional[float]:
    """Extract best-case biodegradable % from EOL assessment."""
    for r in results:
        meta = r.get("metadata", {})
        if isinstance(meta, dict) and meta.get("type") == "end_of_life_assessment":
            oq = r.get("output_quantities", {})
            if isinstance(oq, dict) and "scenarios" in oq:
                scenarios = oq["scenarios"]
                if scenarios:
                    best = max(scenarios, key=lambda s: s.get("paper_mache_biodegraded_pct", 0))
                    return best.get("paper_mache_biodegraded_pct")
    return None


def extract_source_quality(refs: List[Dict]) -> Dict:
    """Compute source quality stats from validation references."""
    if not refs:
        return {"avg": 0, "min": 0, "count": 0, "above_8": 0, "total": 0}
    scores = [r["source_quality_score"] for r in refs]
    return {
        "avg": round(sum(scores) / len(scores), 1),
        "min": min(scores),
        "count": len(scores),
        "above_8": sum(1 for s in scores if s >= 8),
        "total": len(scores),
    }


def validate_sc010() -> ValidationReport:
    """Run all scripts, query DB, validate SC-010 targets."""
    # Phase 1: Run all scripts
    print("=" * 64)
    print("  SC-010 ENVIRONMENTAL VALIDATION")
    print("  Paper Mache + Graphite Composite — Wind Turbine Blade")
    print("=" * 64)
    print("\n--- Phase 1: Running LCA Scripts ---\n")

    script_results = []
    all_scripts_ok = True

    for name, file_name in SCRIPTS:
        if file_name.startswith("ingest_"):
            path = os.path.join(ETL_DIR, file_name)
        else:
            path = os.path.join(SCRIPTS_DIR, file_name)

        if not os.path.exists(path):
            print(f"  SKIP {name} — file not found at {path}")
            continue

        sr = run_script(name, path)
        script_results.append(sr)
        if sr.exit_code != 0:
            all_scripts_ok = False
            if sr.stderr:
                print(f"    STDERR: {sr.stderr[:500]}")

    # Phase 2: Query database
    print("\n--- Phase 2: Querying Database ---\n")
    sim_results = query_simulation_results()
    val_refs = query_validation_references()
    print(f"  Found {len(sim_results)} simulation results")
    print(f"  Found {len(val_refs)} validation references")

    # Phase 3: SC-010 checks
    print("\n--- Phase 3: SC-010 Validation ---\n")

    checks = []

    # C1: Carbon reduction >= 60%
    carbon_reduction = extract_carbon_reduction(sim_results)
    if carbon_reduction is not None:
        c1_pass = carbon_reduction >= SC010_TARGETS["carbon_reduction_min_pct"]
        checks.append(SC010Check(
            criterion_id="SC-010-C1",
            description="Carbon footprint reduction vs. fiberglass (blade material)",
            value=carbon_reduction,
            target=SC010_TARGETS["carbon_reduction_min_pct"],
            unit="%",
            passed=c1_pass,
            source="lca_carbon_comparison.py (DB)",
        ))
        print(f"  C1 Carbon Reduction: {carbon_reduction}% >= {SC010_TARGETS['carbon_reduction_min_pct']}% "
              f"→ {'✅ PASS' if c1_pass else '❌ FAIL'}")
    else:
        print(f"  C1 Carbon Reduction: NOT FOUND in DB — checking script output")
        # Fallback: parse from the script output
        for sr in script_results:
            if "carbon_comparison" in sr.path:
                for line in sr.stdout.split("\n"):
                    if "blade" in line.lower() and "carbon reduction" in line.lower():
                        for part in line.split():
                            try:
                                val = float(part.replace("%", ""))
                                c1_pass = val >= SC010_TARGETS["carbon_reduction_min_pct"]
                                checks.append(SC010Check(
                                    criterion_id="SC-010-C1",
                                    description="Carbon footprint reduction vs. fiberglass (blade material)",
                                    value=val,
                                    target=SC010_TARGETS["carbon_reduction_min_pct"],
                                    unit="%",
                                    passed=c1_pass,
                                    source="lca_carbon_comparison.py (stdout)",
                                ))
                                print(f"  C1 Carbon Reduction: {val}% >= {SC010_TARGETS['carbon_reduction_min_pct']}% "
                                      f"→ {'✅ PASS' if c1_pass else '❌ FAIL'}")
                                break
                            except ValueError:
                                continue
                        break
                break

    # C2: Biodegradable >= 80% (best case)
    biodeg_pct = extract_biodegradable_pct(sim_results)
    if biodeg_pct is not None:
        c2_pass = biodeg_pct >= SC010_TARGETS["biodegradable_min_pct"]
        checks.append(SC010Check(
            criterion_id="SC-010-C2",
            description="Biodegradable within 5 years (best-case scenario)",
            value=biodeg_pct,
            target=SC010_TARGETS["biodegradable_min_pct"],
            unit="%",
            passed=c2_pass,
            source="lca_end_of_life.py (DB)",
        ))
        print(f"  C2 Biodegradable (best): {biodeg_pct}% >= {SC010_TARGETS['biodegradable_min_pct']}% "
              f"→ {'✅ PASS' if c2_pass else '❌ FAIL'}")
    else:
        print(f"  C2 Biodegradable: NOT FOUND in DB — checking script output")
        for sr in script_results:
            if "end_of_life" in sr.path:
                for line in sr.stdout.split("\n"):
                    if "BEST-CASE" in line or "best" in line.lower():
                        for part in line.split():
                            try:
                                val = float(part.replace("%", ""))
                                c2_pass = val >= SC010_TARGETS["biodegradable_min_pct"]
                                checks.append(SC010Check(
                                    criterion_id="SC-010-C2",
                                    description="Biodegradable within 5 years (best-case scenario)",
                                    value=val,
                                    target=SC010_TARGETS["biodegradable_min_pct"],
                                    unit="%",
                                    passed=c2_pass,
                                    source="lca_end_of_life.py (stdout)",
                                ))
                                print(f"  C2 Biodegradable (best): {val}% >= {SC010_TARGETS['biodegradable_min_pct']}% "
                                      f"→ {'✅ PASS' if c2_pass else '❌ FAIL'}")
                                break
                            except ValueError:
                                continue
                        break
                # Fallback: parse the line after "SC-010 (>=80%)"
                for i, line in enumerate(sr.stdout.split("\n")):
                    if "SC-010" in line and "80%" in line:
                        for part in line.split():
                            try:
                                val = float(part.replace("%", "").strip())
                                if val > 0:
                                    checks.append(SC010Check(
                                        criterion_id="SC-010-C2",
                                        description="Biodegradable within 5 years (best-case scenario)",
                                        value=val,
                                        target=SC010_TARGETS["biodegradable_min_pct"],
                                        unit="%",
                                        passed=val >= SC010_TARGETS["biodegradable_min_pct"],
                                        source="lca_end_of_life.py (stdout)",
                                    ))
                                    print(f"  C2 Biodegradable (best): {val}% >= {SC010_TARGETS['biodegradable_min_pct']}% "
                                          f"→ {'✅ PASS' if val >= SC010_TARGETS['biodegradable_min_pct'] else '❌ FAIL'}")
                                    break
                            except ValueError:
                                continue
                        break
                break

    if not any(c.criterion_id == "SC-010-C2" for c in checks):
        checks.append(SC010Check(
            criterion_id="SC-010-C2",
            description="Biodegradable within 5 years (best-case scenario)",
            value=0,
            target=SC010_TARGETS["biodegradable_min_pct"],
            unit="%",
            passed=False,
            source="NOT FOUND",
        ))
        print("  C2 Biodegradable: NOT FOUND → ❌ FAIL (insufficient data)")

    # C3: Source quality >= 8/10
    sq = extract_source_quality(val_refs)
    if sq["count"] > 0:
        c3_pass = sq["min"] >= SC010_TARGETS["source_quality_min"]
        checks.append(SC010Check(
            criterion_id="SC-010-C3",
            description=f"Source quality >= 8/10 (all {sq['count']} references)",
            value=sq["min"],
            target=SC010_TARGETS["source_quality_min"],
            unit="/10",
            passed=c3_pass,
            source=f"{sq['above_8']}/{sq['count']} refs >= 8, avg {sq['avg']}/10",
        ))
        print(f"  C3 Source Quality: min {sq['min']}/10, avg {sq['avg']}/10, "
              f"{sq['above_8']}/{sq['count']} >= 8 → "
              f"{'✅ PASS' if c3_pass else '❌ FAIL'}")
    else:
        checks.append(SC010Check(
            criterion_id="SC-010-C3",
            description="Source quality >= 8/10",
            value=0,
            target=SC010_TARGETS["source_quality_min"],
            unit="/10",
            passed=False,
            source="No validation references found in DB",
        ))
        print("  C3 Source Quality: NO REFERENCES → ❌ FAIL")

    # Overall
    all_lca_ok = all(s.exit_code == 0 for s in script_results)
    all_sc010_ok = all(c.passed for c in checks)
    passed_checks = sum(1 for c in checks if c.passed)
    total_checks = len(checks)

    print(f"\n  {'═' * 60}")
    print(f"  SC-010 VALIDATION SUMMARY: {passed_checks}/{total_checks} criteria passed")
    print(f"  {'─' * 40}")
    for c in checks:
        print(f"  {'✅' if c.passed else '❌'} {c.criterion_id}: {c.value}{c.unit} "
              f"(target: >= {c.target}{c.unit})")
    print(f"  {'─' * 40}")
    verdict = "✅ SC-010 PASS" if all_sc010_ok else "❌ SC-010 FAIL"
    print(f"  {verdict}")
    print("")

    return ValidationReport(
        timestamp=__import__("datetime").datetime.now().isoformat(),
        scripts=script_results,
        checks=checks,
        all_scripts_passed=all_lca_ok,
        all_checks_passed=all_sc010_ok,
        summary=verdict,
    )


def format_report(vr: ValidationReport) -> str:
    """Format the validation report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  SC-010 ENVIRONMENTAL VALIDATION REPORT")
    lines.append(f"  Generated: {vr.timestamp}")
    lines.append("=" * 64)

    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  SCRIPTS EXECUTED: {len(vr.scripts)}")
    lines.append(f"  {'─' * 60}")
    for s in vr.scripts:
        status = "✅" if s.exit_code == 0 else "❌"
        lines.append(f"  {status} {s.name:<30} exit={s.exit_code}")
    if not vr.all_scripts_passed:
        lines.append(f"\n  ⚠ WARNING: Some scripts failed — SC-010 data may be incomplete")

    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  SC-010 CRITERIA: {sum(1 for c in vr.checks if c.passed)}/{len(vr.checks)} passed")
    lines.append(f"  {'─' * 60}")
    for c in vr.checks:
        icon = "✅" if c.passed else "❌"
        lines.append(f"  {icon} {c.criterion_id}: {c.description}")
        lines.append(f"      Value: {c.value}{c.unit}  Target: >= {c.target}{c.unit}")
        lines.append(f"      Source: {c.source}")
        lines.append("")

    lines.append(f"  {'═' * 60}")
    lines.append(f"  VERDICT: {vr.summary}")
    lines.append(f"  {'═' * 60}")
    lines.append("")

    return "\n".join(lines)


def main():
    result = validate_sc010()
    print("\n" + "=" * 64)
    print(format_report(result))
    return 0 if result.all_checks_passed else 1


if __name__ == "__main__":
    main()
