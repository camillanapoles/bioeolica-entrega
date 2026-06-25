#!/usr/bin/env python3
"""
Material Property Comparison Visualization — Bioeolica Project.

Generates comparative bar charts for material properties
(baseline paper mache vs. graphite composite) from the SQLite database.

Usage:
    python src/visualization/plot_property_comparison.py [--output-dir output/]
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.common.database import database

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "figures")


def get_property_comparison(db) -> List[Dict[str, Any]]:
    """Get test results grouped by property for baseline vs composite."""
    rows = db.execute(
        """SELECT ms.specimen_type, tr.property_measured,
                  tr.value, tr.unit, tr.uncertainty
           FROM test_results tr
           JOIN material_specimens ms ON tr.specimen_id = ms.id
           ORDER BY tr.property_measured, ms.specimen_type"""
    ).fetchall()
    return [dict(r) for r in rows]


def plot_property_comparison(data: List[Dict[str, Any]],
                              output_dir: str = OUTPUT_DIR):
    """Plot baseline vs composite bar chart per property."""
    os.makedirs(output_dir, exist_ok=True)

    # Group by property
    props: Dict[str, Dict[str, List[float]]] = {}
    for d in data:
        p = d["property_measured"]
        t = d["specimen_type"]
        if p not in props:
            props[p] = {"baseline": [], "composite": [], "unit": d["unit"]}
        if t in props[p]:
            props[p][t].append(d["value"])

    if not props:
        print("  No property data found for visualization")
        return False

    fig, axes = plt.subplots(1, len(props), figsize=(5 * len(props), 5))
    if len(props) == 1:
        axes = [axes]

    for ax, (prop_name, pdata) in zip(axes, sorted(props.items())):
        baseline_vals = pdata.get("baseline", [])
        composite_vals = pdata.get("composite", [])
        unit = pdata.get("unit", "")

        baseline_mean = sum(baseline_vals) / len(baseline_vals) if baseline_vals else 0
        composite_mean = sum(composite_vals) / len(composite_vals) if composite_vals else 0

        categories = ["Baseline", "Composite"]
        values = [baseline_mean, composite_mean]
        colors = ["#4A90D9", "#D94A4A"]

        bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor="black")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

        # Improvement annotation
        if baseline_mean > 0:
            improvement = ((composite_mean - baseline_mean) / baseline_mean) * 100
            color = "green" if improvement > 0 else "red"
            sign = "+" if improvement > 0 else ""
            ax.text(0.5, 0.85, f"{sign}{improvement:.1f}%", transform=ax.transAxes,
                    fontsize=12, fontweight="bold", color=color, ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

        ax.set_title(prop_name.replace("_", " ").title(), fontsize=13, fontweight="bold")
        ax.set_ylabel(f"Value ({unit})" if unit else "Value")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Material Property Comparison: Baseline vs Graphite Composite",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()

    path = os.path.join(output_dir, "property_comparison.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved property comparison chart: {path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Material Property Comparison Plot")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    if not HAS_MPL:
        print("  matplotlib not installed — skipping chart generation")
        return 0

    with database() as db:
        data = get_property_comparison(db)

    if not data:
        print("  No test result data in database")
        return 0

    plot_property_comparison(data, args.output_dir)
    return 0


if __name__ == "__main__":
    main()
