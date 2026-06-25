#!/usr/bin/env python3
"""
VAWT vs Archimedes turbine comparison for small wind (5-15 kW)
in semi-arid NE Brazil.

8 weighted criteria:
  energy_yield, cut_in_speed, cost, repairability,
  structural_complexity, noise, visual_impact, survivability

Outputs weighted score, recommendation, and SQLite registration.
"""

import json
import sys
import os
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.registry import create_object
from src.common.database import database

# ---- data ---- #

CRITERIA = [
    "energy_yield",
    "cut_in_speed",
    "cost",
    "repairability",
    "structural_complexity",
    "noise",
    "visual_impact",
    "survivability",
]

WEIGHTS = {
    "energy_yield": 0.20,
    "cut_in_speed": 0.10,
    "cost": 0.20,
    "repairability": 0.10,
    "structural_complexity": 0.10,
    "noise": 0.10,
    "visual_impact": 0.05,
    "survivability": 0.15,
}

# Scores 1-10 (10 = best for small wind in semi-arid NE Brazil)
VAWT_SCORES = {
    "energy_yield": 7,
    "cut_in_speed": 8,  # VAWT ~2.5 m/s cut-in, omnidirectional
    "cost": 8,  # Simple H-rotor, fewer moving parts, lower tooling
    "repairability": 9,  # Low height, simple structure, local repair possible
    "structural_complexity": 8,  # Straight blades, few components
    "noise": 8,  # Lower tip-speed ratio → quieter
    "visual_impact": 6,  # Larger swept area at low height
    "survivability": 7,  # Good storm survival (low RPM), no yaw mechanism
}

ARCHIMEDES_SCORES = {
    "energy_yield": 8,  # Higher peak Cp (0.25-0.35)
    "cut_in_speed": 6,  # HAWT-style ~3.5 m/s
    "cost": 5,  # Spiral/screw geometry → more complex tooling
    "repairability": 5,  # At height, spiral repair difficult locally
    "structural_complexity": 5,  # Complex curved geometry
    "noise": 6,  # Higher TSR → more aerodynamic noise
    "visual_impact": 7,  # Smaller swept area, looks like chimney
    "survivability": 6,  # Yaw + furling mechanisms = failure points
}


# ---- scoring ---- #

@dataclass
class ComparisonResult:
    vawt_weighted: float
    archimedes_weighted: float
    vawt_scores: dict
    archimedes_scores: dict
    weights: dict
    winner: str
    margin: float
    detail: list = field(default_factory=list)


def compare(vawt=VAWT_SCORES, archimedes=ARCHIMEDES_SCORES, weights=WEIGHTS) -> ComparisonResult:
    vawt_w = sum(weights[c] * vawt[c] for c in CRITERIA)
    arch_w = sum(weights[c] * archimedes[c] for c in CRITERIA)

    detail = []
    for c in CRITERIA:
        detail.append({
            "criterion": c,
            "weight": weights[c],
            "vawt": vawt[c],
            "archimedes": archimedes[c],
            "vawt_weighted": round(weights[c] * vawt[c], 3),
            "archimedes_weighted": round(weights[c] * archimedes[c], 3),
        })

    winner = "VAWT" if vawt_w > arch_w else "Archimedes"
    margin = abs(vawt_w - arch_w)

    return ComparisonResult(
        vawt_weighted=round(vawt_w, 2),
        archimedes_weighted=round(arch_w, 2),
        vawt_scores=vawt,
        archimedes_scores=archimedes,
        weights=weights,
        winner=winner,
        margin=round(margin, 2),
        detail=detail,
    )


def report(result: ComparisonResult) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  VAWT vs Archimedes Comparison — Small Wind (5-15 kW)")
    lines.append("  Semi-arid NE Brazil context")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"{'Criterion':<30} {'Weight':>7} {'VAWT':>7} {'Arch':>7}")
    lines.append("-" * 55)
    for d in result.detail:
        lines.append(
            f"{d['criterion']:<30} {d['weight']:>7.2f} {d['vawt']:>7} {d['archimedes']:>7}"
        )
    lines.append("-" * 55)
    lines.append(
        f"{'WEIGHTED TOTAL':<30} {'':>7} {result.vawt_weighted:>7.2f} {result.archimedes_weighted:>7.2f}"
    )
    lines.append("")
    lines.append(f"  WINNER: {result.winner} (margin: {result.margin})")
    lines.append("")

    # Recommendation
    lines.append("  --- Recommendation ---")
    if result.winner == "VAWT":
        lines.append("  VAWT H-rotor Darrieus is recommended for:")
        lines.append("    • Rural communities with limited maintenance access")
        lines.append("    • Low wind speed sites (3-6 m/s mean)")
        lines.append("    • DIY / local fabrication capability")
        lines.append("    • Gusty / turbulent conditions")
        lines.append(f"  Weighted score: {result.vawt_weighted} vs {result.archimedes_weighted}")
    else:
        lines.append("  Archimedes screw-type is recommended for:")
        lines.append("    • Slightly higher wind sites (>6 m/s mean)")
        lines.append("    • Where visual impact is primary concern")
        lines.append("    • Grid-connected with professional O&M")
        lines.append(f"  Weighted score: {result.archimedes_weighted} vs {result.vawt_weighted}")
    lines.append("")

    return "\n".join(lines)


def register_comparison(result: ComparisonResult) -> str:
    """Store comparison result in SQLite."""
    data = {
        "vawt_weighted": result.vawt_weighted,
        "archimedes_weighted": result.archimedes_weighted,
        "winner": result.winner,
        "margin": result.margin,
        "weights": result.weights,
        "vawt_scores": result.vawt_scores,
        "archimedes_scores": result.archimedes_scores,
        "detail": result.detail,
    }

    model_id = create_object(
        "computational_model",
        tags=["turbine_comparison", "scoring_model"],
        metadata={"type": "weighted_scoring",
                   "source": "src/02-wind-energy/comparison/turbine_comparison.py"},
    )
    obj_id = create_object(
        "simulation_result",
        tags=["turbine_comparison", "vawt_vs_archimedes"],
        metadata={"source": "src/02-wind-energy/comparison/turbine_comparison.py"},
    )

    with database() as db:
        db.execute(
            """INSERT INTO computational_models
               (id, model_type, domain, solver_software, solver_version,
                boundary_conditions, material_model, material_properties)
               VALUES (?, 'analytical', 'coupled',
                       'python_analytical', '1.0',
                       'N/A_analytical', 'N/A_analytical', 'N/A_analytical')""",
            (model_id,),
        )
        db.execute(
            """INSERT INTO simulation_results
               (id, model_id, run_timestamp, convergence_metric, convergence_threshold,
                mesh_convergence_pct, output_quantities, notes)
               VALUES (?, ?, datetime('now'), 'weighted_score', NULL, NULL, ?, ?)""",
            (obj_id, model_id, json.dumps(data), f"Comparison winner: {result.winner} (margin={result.margin})"),
        )
        db.commit()

    return obj_id


def main():
    result = compare()
    print(report(result))

    comp_id = register_comparison(result)
    print(f"  Registered comparison: {comp_id}")
    print(f"\n  → Winner: {result.winner} (score delta: {result.margin})")
    return 0 if result.winner == "VAWT" else 1


if __name__ == "__main__":
    sys.exit(main())
