#!/usr/bin/env python3
"""
SU2 cross-validation runner for VAWT H-rotor Darrieus.

Generates SU2 configs, then (optionally) runs SU2_CFD for
each operating point to validate OpenFOAM SRF results.

Usage:
  python3 generate_su2_configs.py       # Generate .cfg files only
  python3 run_su2_validation.py         # Generate + run (requires SU2)
"""

from generate_su2_configs import generate_su2_configs
import subprocess
import os

SU2_SOLVER = os.environ.get("SU2_CFD", "SU2_CFD")


def main():
    output_dir = "."
    generate_su2_configs(output_dir)

    # Check if SU2 is available
    try:
        subprocess.run([SU2_SOLVER, "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"\nSU2 not found at '{SU2_SOLVER}'. Configs generated but not run.")
        print(f"Install SU2 or set SU2_CFD env var.")
        return

    # Run each config
    cfg_files = sorted(f for f in os.listdir(output_dir) if f.endswith(".cfg"))
    for cfg in cfg_files:
        print(f"\n--- Running SU2: {cfg} ---")
        log = cfg.replace(".cfg", ".log")
        with open(log, "w") as lf:
            result = subprocess.run(
                [SU2_SOLVER, cfg], cwd=output_dir, stdout=lf, stderr=subprocess.STDOUT
            )
        status = "PASS" if result.returncode == 0 else f"FAIL (code {result.returncode})"
        print(f"  {cfg} → {status} (log: {log})")


if __name__ == "__main__":
    main()
