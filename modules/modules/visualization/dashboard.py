#!/usr/bin/env python3
"""
Visualization Dashboard — Bioeolica Project.

Entry point that runs all visualization scripts in sequence.
Generates property comparison charts, PQMS radar charts,
and SC-010 environmental summary charts.

Usage:
    python src/visualization/dashboard.py [--output-dir output/figures]
"""

import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "figures")


def run_script(name: str, path: str, args: list = None) -> bool:
    """Run a Python script and return True if successful."""
    cmd = [sys.executable, path]
    if args:
        cmd.extend(args)
    print(f"  Running {name}...", end=" ")
    sys.stdout.flush()
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("OK")
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")
        return True
    else:
        print("FAIL")
        for line in result.stderr.strip().split("\n"):
            print(f"    ERROR: {line}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Visualization Dashboard")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 64)
    print("  BIOEOLICA — VISUALIZATION DASHBOARD")
    print(f"  Generated: {datetime.now().isoformat()}")
    print(f"  Output:    {args.output_dir}")
    print("=" * 64)

    scripts = [
        ("Property Comparison", os.path.join(SCRIPT_DIR, "plot_property_comparison.py")),
        ("PQMS Radar", os.path.join(SCRIPT_DIR, "plot_pqms_radar.py")),
    ]

    success = 0
    for name, path in scripts:
        if os.path.exists(path):
            if run_script(name, path, ["--output-dir", args.output_dir]):
                success += 1
        else:
            print(f"  SKIP {name} — not found at {path}")

    print(f"\n  Dashboard complete: {success}/{len(scripts)} charts generated")
    print(f"  Figures saved to: {args.output_dir}")
    print()

    return 0 if success == len(scripts) else 1


if __name__ == "__main__":
    main()
