#!/usr/bin/env python3
"""
Post-process Archimedes TSR sweep results.

Aggregates force coefficients across all (TSR, V) combinations
and produces a comparison table for VAWT vs Archimedes.
"""

import json
import glob
import re
import os
from pathlib import Path


def extract_cp(patch_file: str) -> float | None:
    """Extract Cp from forceCoeffs output. Archimedes: Cp = -Cd (drag device)."""
    try:
        with open(patch_file) as f:
            text = f.read()
        # Look for Cm (moment coefficient) — Archimedes is a lift/drag hybrid
        matches = re.findall(r"Cm\s+=\s+([-\d.eE+]+)", text)
        if matches:
            return float(matches[-1])
        matches_cp = re.findall(r"Cp\s+=\s+([-\d.eE+]+)", text)
        if matches_cp:
            return float(matches_cp[-1])
    except (FileNotFoundError, ValueError, IndexError):
        return None
    return None


def main():
    results = []

    # Scan TSR_*/ directories
    for case_dir in sorted(glob.glob("TSR_*_V*")):
        match = re.match(r"TSR_([\d.]+)_V([\d.]+)", os.path.basename(case_dir))
        if not match:
            continue
        tsr, v = float(match.group(1)), float(match.group(2))

        # Find latest forceCoeffs output
        coeffs_dir = Path(case_dir) / "postProcessing" / "forceCoeffs_archimedes"
        if not coeffs_dir.exists():
            print(f"  WARN: no forceCoeffs for {case_dir}")
            continue

        time_dirs = sorted(coeffs_dir.glob("[0-9]*"))
        if not time_dirs:
            print(f"  WARN: no time directories in {coeffs_dir}")
            continue

        patch_file = time_dirs[-1] / "forceCoeffs.dat"
        if not patch_file.exists():
            patch_file = time_dirs[-1] / "coefficient.dat"

        cp = extract_cp(str(patch_file)) if patch_file.exists() else None
        cp = cp or 0.0
        results.append({"TSR": tsr, "V": v, "Cp": cp})

        status = f"Cp={cp:.4f}" if cp else "no data"
        print(f"  TSR={tsr:.1f} V={v:.1f}m/s → {status}")

    # Summary table
    if results:
        print("\n--- Archimedes TSR Sweep Summary ---")
        print(f"{'TSR':>6} {'V(m/s)':>8} {'Cp':>8}")
        print("-" * 24)
        for r in results:
            print(f"{r['TSR']:>6.1f} {r['V']:>8.1f} {r['Cp']:>8.4f}")

        avg_cp = sum(r["Cp"] for r in results) / len(results)
        best = max(results, key=lambda r: r["Cp"])
        print(f"\n  Mean Cp: {avg_cp:.4f}")
        print(f"  Best Cp: {best['Cp']:.4f} @ TSR={best['TSR']:.1f}, V={best['V']:.1f}m/s")
    else:
        print("No results found. Run Allrun first.")


if __name__ == "__main__":
    main()
