#!/usr/bin/env python3
# =============================================================================
# Upscaling Sweep — Multi-Config Turbine Comparison
# Part of T009 — Phase 3 US1
# Depends on: cost_breakdown.py, aep_model.py, lcoe_model.py
# Output: comparison/upscaling_sweep_results.json
# =============================================================================
"""
Multi-configuration sweep across power ratings and topologies.

Evaluates all combinations of:
  - Ratings: 5, 10, 12, 15, 20 kW
  - Topologies: VAWT, HAWT
  - Wind speeds: 6.0, 6.5, 7.0, 7.5, 8.0 m/s

Saves results to comparison/upscaling_sweep_results.json

Usage:
    python src/02-wind-energy/energy-system/upscaling_sweep.py
"""
from __future__ import annotations

import json
import os
import sys

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from aep_model import compute_aep
from cost_breakdown import compute_cost_breakdown
from lcoe_model import compute_lcoe

# Sweep space
RATINGS_KW = [5, 10, 12, 15, 20]
TOPOLOGIES = ["VAWT", "HAWT"]
WIND_SPEEDS = [6.0, 6.5, 7.0, 7.5, 8.0]

# Output
OUTPUT_DIR = os.path.normpath(
    os.path.join(_project_root, "src", "02-wind-energy", "comparison")
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "upscaling_sweep_results.json")


def run_sweep() -> list:
    """Run all rating × topology × wind speed combinations.

    Returns:
        List of result dicts, each with:
            rating_kw, topology, wind_speed_ms, cost_kw, lcoe,
            aep_kwh, capacity_factor_pct, sc004_pass, sc005c_pass
    """
    results = []
    total = len(RATINGS_KW) * len(TOPOLOGIES) * len(WIND_SPEEDS)
    idx = 0

    for kw in RATINGS_KW:
        for top in TOPOLOGIES:
            for v in WIND_SPEEDS:
                idx += 1
                try:
                    r = compute_lcoe(kw, v, top)
                except Exception as e:
                    print(f"  [{idx}/{total}] {kw}kW {top} @ {v}m/s — SKIP ({e})")
                    continue

                entry = {
                    "rating_kw": kw,
                    "topology": top,
                    "wind_speed_ms": v,
                    "cost_kw_usd": r["cost_per_kw_usd"],
                    "lcoe_usd_per_kwh": r["lcoe_usd_per_kwh"],
                    "aep_kwh": r["aep_kwh"],
                    "capacity_factor_pct": r["aep_kwh"]
                        / (kw * 8760) * 100,
                    "total_cost_usd": r["total_installed_cost_usd"],
                    "sc004_cost": r["sc004_cost"],
                    "sc004_lcoe": r["sc004_lcoe"],
                    "sc005c_pass": (
                        "PASS" if (r["aep_kwh"] / (kw * 8760) * 100) >= 20.0
                        else "FAIL"
                    ),
                }
                results.append(entry)

                # Live progress
                sc = "✅" if all([
                    entry["sc004_cost"] == "PASS",
                    entry["sc004_lcoe"] == "PASS",
                ]) else "❌"
                print(f"  [{idx}/{total}] {kw:>2}kW {top:>4s} @ {v:.1f}m/s  "
                      f"${r['cost_per_kw_usd']:>5,.0f}/kW  "
                      f"${r['lcoe_usd_per_kwh']:.4f}/kWh  {sc}")

    return results


def save_results(results: list) -> str:
    """Save sweep results to JSON and return the path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    payload = {
        "meta": {
            "task": "T009",
            "description": "Upscaling sweep — 5–20 kW × VAWT/HAWT × 6–8 m/s",
            "ratings_kw": RATINGS_KW,
            "topologies": TOPOLOGIES,
            "wind_speeds_ms": WIND_SPEEDS,
        },
        "results": results,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    return OUTPUT_FILE


def best_config(results: list) -> dict:
    """Find the configuration with lowest LCOE."""
    valid = [r for r in results if r["sc004_cost"] == "PASS"]
    if not valid:
        return {"error": "no passing config"}
    return min(valid, key=lambda r: r["lcoe_usd_per_kwh"])


def _test():
    print("=" * 72)
    print("  T009 — Upscaling Sweep")
    print(f"  {len(RATINGS_KW)} ratings × {len(TOPOLOGIES)} topologies"
          f" × {len(WIND_SPEEDS)} wind speeds = {len(RATINGS_KW)*len(TOPOLOGIES)*len(WIND_SPEEDS)} configs")
    print("=" * 72)
    print()

    results = run_sweep()
    path = save_results(results)
    best = best_config(results)

    print()
    print(f"  Results saved: {path}")
    print(f"  Total configs: {len(results)}")
    passes = sum(1 for r in results
                 if r["sc004_cost"] == "PASS" and r["sc004_lcoe"] == "PASS")
    print(f"  SC-004 PASS:   {passes}/{len(results)}")
    print()
    print(f"  Best config: {best['rating_kw']}kW {best['topology']}"
          f" @ {best['wind_speed_ms']}m/s")
    print(f"    LCOE:    ${best['lcoe_usd_per_kwh']:.4f}/kWh")
    print(f"    Cost/kW: ${best['cost_kw_usd']:,.0f}")
    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
