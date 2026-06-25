#!/usr/bin/env python3
"""
PQMS Radar Chart Visualization — Bioeolica Project.

Generates a radar (spider) chart of PQMS dimension scores
for one or more objects in the database.

Usage:
    python src/visualization/plot_pqms_radar.py [--object-id <uuid>] [--output-dir output/]
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
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "figures")

PQMS_DIMENSIONS = [
    "D1_completude", "D2_profundidade", "D3_rigor",
    "D4_rastreabilidade", "D5_conhecimento", "D6_integracao",
    "D7_qualidade_numerica", "D8_impacto", "D9_vies", "D10_ensino",
    "D11_velocidade", "D12_satisfacao", "D13_inovacao",
]

DIM_LABELS = {
    "D1_completude": "Completude",
    "D2_profundidade": "Profundidade",
    "D3_rigor": "Rigor",
    "D4_rastreabilidade": "Rastreabilidade",
    "D5_conhecimento": "Conhecimento",
    "D6_integracao": "Integração",
    "D7_qualidade_numerica": "Qualidade\nNumérica",
    "D8_impacto": "Impacto",
    "D9_vies": "Viés",
    "D10_ensino": "Ensino",
    "D11_velocidade": "Velocidade",
    "D12_satisfacao": "Satisfação",
    "D13_inovacao": "Inovação",
}

TARGET_9_5 = 9.5
MIN_8_5 = 8.5


def get_dimension_scores_for_objects(db) -> List[Dict[str, Any]]:
    """Get all objects with their dimension scores."""
    objects = db.execute(
        """SELECT DISTINCT qs.object_id, o.object_type, o.quality_score as aggregate
           FROM quality_scores qs
           JOIN objects o ON qs.object_id = o.id
           ORDER BY o.object_type"""
    ).fetchall()

    results = []
    for obj in objects:
        oid = obj["object_id"]
        scores = db.execute(
            "SELECT dimension, score FROM quality_scores WHERE object_id = ?",
            (oid,),
        ).fetchall()
        score_dict = {r["dimension"]: r["score"] for r in scores}
        results.append({
            "id": oid,
            "type": obj["object_type"],
            "aggregate": obj["aggregate"],
            "scores": score_dict,
        })
    return results


def plot_pqms_radar(objects: List[Dict[str, Any]],
                     output_dir: str = OUTPUT_DIR):
    """Generate PQMS radar chart for all scored objects."""
    os.makedirs(output_dir, exist_ok=True)

    if not HAS_MPL:
        print("  matplotlib not installed — skipping radar chart")
        return

    n_objects = len(objects)
    if n_objects == 0:
        print("  No scored objects found")
        return

    # One chart per object
    for obj in objects:
        oid_short = obj["id"][:8]
        otype = obj["type"]
        aggregate = obj["aggregate"]
        scores = obj["scores"]

        # Build radar
        dims = [d for d in PQMS_DIMENSIONS if d in scores]
        if not dims:
            continue

        values = [scores[d] for d in dims]
        n_dims = len(dims)

        # Close the polygon
        angles = [n / n_dims * 2 * np.pi for n in range(n_dims)]
        angles += angles[:1]
        plot_values = values + values[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Draw axis lines
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([DIM_LABELS.get(d, d) for d in dims], fontsize=9)

        # Y-axis (0-10)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)
        ax.yaxis.set_tick_params(labelsize=8)

        # Target zone (>= 9.5)
        ax.fill_between(np.linspace(0, 2 * np.pi, 100),
                        9.5, 10, color="green", alpha=0.08)

        # Minimum threshold (8.5)
        ax.plot(np.linspace(0, 2 * np.pi, 100),
                [8.5] * 100, color="orange", linestyle="--", linewidth=0.8, alpha=0.6)

        # Data
        ax.plot(angles, plot_values, "o-", linewidth=2, color="#4A90D9", markersize=6)
        ax.fill(angles, plot_values, alpha=0.15, color="#4A90D9")

        # Annotate values
        for angle, val, dim in zip(angles[:-1], values, dims):
            ax.annotate(f"{val:.1f}",
                        (angle, val),
                        fontsize=8, ha="center", va="bottom",
                        fontweight="bold", color="#2C5F8A")

        status = "PASS" if (aggregate and aggregate >= 9.5) else "FAIL"
        ax.set_title(f"PQMS Radar — {otype}\n"
                     f"Aggregate: {aggregate:.2f}/10 — {'✅' if aggregate and aggregate >= 9.5 else '❌'} {status}",
                     fontsize=13, fontweight="bold", pad=20)

        fig.tight_layout()
        path = os.path.join(output_dir, f"pqms_radar_{oid_short}_{otype}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved PQMS radar: {path}")

    # Combined chart if multiple objects
    if n_objects > 1:
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={"projection": "polar"})
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)

        colors = plt.cm.Set2(np.linspace(0, 1, n_objects))
        for i, obj in enumerate(objects):
            scores = obj["scores"]
            dims = [d for d in PQMS_DIMENSIONS if d in scores]
            if not dims:
                continue
            values = [scores[d] for d in dims]
            angles = [n / len(dims) * 2 * np.pi for n in range(len(dims))]
            angles += angles[:1]
            plot_values = values + values[:1]
            ax.plot(angles, plot_values, "o-", linewidth=1.5,
                    color=colors[i], markersize=4, alpha=0.8,
                    label=f"{obj['type']} ({obj['aggregate']:.1f})")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([DIM_LABELS.get(d, d) for d in dims], fontsize=9)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), fontsize=9)
        ax.set_title("PQMS Radar — All Objects (Combined)",
                     fontsize=14, fontweight="bold", pad=20)

        fig.tight_layout()
        path = os.path.join(output_dir, "pqms_radar_combined.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved combined radar: {path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PQMS Radar Chart Generator")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--object-id", default=None, help="Specific object UUID")
    args = parser.parse_args()

    if not HAS_MPL:
        print("  matplotlib not installed — install with: pip install matplotlib numpy")
        return 0

    with database() as db:
        objects = get_dimension_scores_for_objects(db)

    if args.object_id:
        objects = [o for o in objects if o["id"] == args.object_id]

    if not objects:
        print("  No scored objects found in database")
        return 0

    plot_pqms_radar(objects, args.output_dir)
    return 0


if __name__ == "__main__":
    main()
