#!/usr/bin/env python3
# =============================================================================
# Comparison Report — Composite Biomaterial for Wind Energy
# Phase 2 — Material Characterization | T034
# Baseline: paper mache + PVA only
# Composite: paper mache + PVA + graphite coating (blasted)
# SC-001 targets: hardness +40%, flexural_modulus +25%
# =============================================================================
"""
Comparative property analysis (baseline vs graphite-coated composite)
generating percentage-improvement tables and SC-001 compliance checks.

Usage:
    python comparison_report.py

    Prints a formatted comparison table and SC-001 PASS/FAIL status.
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PropertyComparison:
    """Comparison of a single property between baseline and composite."""

    property_name: str
    baseline_value: float
    composite_value: float
    unit: str
    improvement_pct: float = field(init=False)
    sc001_target: Optional[float] = None   # Minimum % improvement required

    def __post_init__(self) -> None:
        if self.baseline_value == 0.0:
            self.improvement_pct = 0.0
        else:
            self.improvement_pct = (
                (self.composite_value - self.baseline_value)
                / self.baseline_value
                * 100.0
            )


# ---------------------------------------------------------------------------
# Source data
# ---------------------------------------------------------------------------

def get_comparison_data() -> List[PropertyComparison]:
    """Return all property comparisons (baseline vs composite)."""
    return [
        PropertyComparison(
            property_name="tensile_strength",
            baseline_value=9.8,
            composite_value=12.5,
            unit="MPa",
        ),
        PropertyComparison(
            property_name="flexural_modulus",
            baseline_value=2.9,
            composite_value=3.8,
            unit="GPa",
            sc001_target=25.0,
        ),
        PropertyComparison(
            property_name="compressive_strength",
            baseline_value=14.2,
            composite_value=18.0,
            unit="MPa",
        ),
        PropertyComparison(
            property_name="hardness",
            baseline_value=58.0,
            composite_value=72.0,
            unit="Shore D",
            sc001_target=40.0,
        ),
        PropertyComparison(
            property_name="density",
            baseline_value=750.0,
            composite_value=850.0,
            unit="kg/m3",
        ),
    ]


# ---------------------------------------------------------------------------
# Table generation
# ---------------------------------------------------------------------------

def generate_comparison_table(comparisons: List[PropertyComparison]) -> str:
    """Return a formatted markdown comparison table.

    Columns: Property | Baseline | Composite | Unit | Change (%) | SC-001
    """
    lines: List[str] = []
    lines.append("| Property | Baseline | Composite | Unit | Change (%) | SC-001 Target |")
    lines.append("|----------|----------|-----------|------|------------|---------------|")

    for c in comparisons:
        change_str = f"{c.improvement_pct:+.1f}%"
        if c.sc001_target is not None:
            sc001_str = f"{c.sc001_target:+.0f}% ({_status_marker(c)})"
        else:
            sc001_str = "---"

        lines.append(
            f"| {c.property_name:20s}"
            f" | {c.baseline_value:<8.1f}"
            f" | {c.composite_value:<9.1f}"
            f" | {c.unit:<4s}"
            f" | {change_str:>10s}"
            f" | {sc001_str:>13s} |"
        )

    return "\n".join(lines)


def _status_marker(c: PropertyComparison) -> str:
    """Return 'PASS' or 'FAIL' for SC-001 target."""
    if c.sc001_target is None:
        return "---"
    return "PASS" if c.improvement_pct >= c.sc001_target else "FAIL"


# ---------------------------------------------------------------------------
# SC-001 compliance
# ---------------------------------------------------------------------------

def check_sc001_targets(comparisons: List[PropertyComparison]) -> Dict[str, object]:
    """Check SC-001 requirements against current property data.

    SC-001 targets checked:
      - hardness improvement        >= +40 %  (composite 72 vs baseline 58 = +24.1 %)
      - flexural_modulus improvement >= +25 % (composite 3.8 vs baseline 2.9 = +31.0 %)

    Returns
    -------
    dict with keys:
        ``targets``  — list of per-target results
        ``overall``  — "PASS"|"FAIL"
        ``summary``  — textual summary
    """
    targets: List[Dict[str, object]] = []
    all_pass = True

    for c in comparisons:
        if c.sc001_target is None:
            continue

        achieved = c.improvement_pct >= c.sc001_target
        if not achieved:
            all_pass = False

        gap = max(c.sc001_target - c.improvement_pct, 0.0)

        targets.append({
            "property": c.property_name,
            "target_pct": c.sc001_target,
            "achieved_pct": round(c.improvement_pct, 1),
            "status": "PASS" if achieved else "FAIL",
            "gap_pct": round(gap, 1),
        })

    overall = "PASS" if all_pass else "FAIL"

    # Build summary
    summary_lines: List[str] = []
    summary_lines.append("SC-001 Target Verification")
    summary_lines.append("")
    for t in targets:
        mark = "PASS" if t["status"] == "PASS" else "FAIL"
        summary_lines.append(
            f"  {t['property']:25s}: target {t['target_pct']:+.0f}% "
            f"achieved {t['achieved_pct']:+.1f}%  [{mark}]"
        )
        if t["status"] == "FAIL":
            summary_lines.append(
                f"  {'':25s}  gap: {t['gap_pct']:.1f} percentage points below target"
            )

    summary_lines.append(f"\n  Overall: {overall}")
    if overall == "FAIL":
        summary_lines.append(
            "  Hardness SC-001 is NOT yet met.  The +24.1 % improvement "
            "from graphite blasting falls short of the +40 % target. "
            "Recommended actions: increase coating thickness, optimise "
            "particle size distribution, or investigate alternative "
            "surface treatments."
        )

    return {
        "targets": targets,
        "overall": overall,
        "summary": "\n".join(summary_lines),
    }


# ---------------------------------------------------------------------------
# Full report text
# ---------------------------------------------------------------------------

def generate_report_text(
    comparisons: List[PropertyComparison],
    sc001_results: Dict[str, object],
) -> str:
    """Return a structured plain-text report for printing or saving."""
    lines: List[str] = []
    sep = "=" * 70

    lines.append(sep)
    lines.append("  MATERIAL COMPARISON REPORT")
    lines.append("  Baseline:  paper mache + PVA binder")
    lines.append("  Composite: paper mache + PVA + graphite coating (blasted)")
    lines.append(sep)

    lines.append("")
    lines.append(generate_comparison_table(comparisons))
    lines.append("")

    lines.append(sep)
    lines.append("  SC-001 COMPLIANCE CHECK")
    lines.append(sep)
    lines.append("")

    # noinspection PyTypeChecker
    lines.append(str(sc001_results["summary"]))

    lines.append("")
    lines.append(sep)
    lines.append("  KEY OBSERVATIONS")
    lines.append(sep)
    lines.append("")
    lines.append("  1. Graphite coating improves all mechanical properties "
                 "(+13 % to +31 %).")
    lines.append("  2. Flexural modulus (+31.0 %) exceeds the SC-001 +25 % "
                 "target — PASS.")
    lines.append("  3. Hardness (+24.1 %) falls short of the SC-001 +40 % "
                 "target — FAIL.")
    lines.append("  4. Density increases by +13.3 % (750 -> 850 kg/m3), "
                 "which may affect buoyancy and handling.")
    lines.append("  5. The hardness gap (-15.9 pp) suggests optimisation "
                 "opportunities in coating thickness or particle grading.")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate comparison report and print to stdout."""
    comparisons = get_comparison_data()
    sc001_results = check_sc001_targets(comparisons)

    report = generate_report_text(comparisons, sc001_results)
    print()
    print(report)
    print()

    # Also print a machine-readable summary
    print("  VERDICT", sc001_results["overall"])
    for t in sc001_results["targets"]:  # type: ignore[union-attr]
        print(f"  {t['property']:25s}  target={t['target_pct']:+.0f}%  "
              f"achieved={t['achieved_pct']:+.1f}%  "
              f"status={t['status']}")
    print()


if __name__ == "__main__":
    main()
