#!/usr/bin/env python3
"""
run_optimization.py — CLI entry point for topology optimization.

Usage:
    python -m src.topopt.run_optimization [--nelx 80] [--nely 40] [--vol-frac 0.3]
                                          [--penal 3.0] [--max-iter 200] [--tol 1e-4]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import openmdao.api as om
from .topopt_group import TopOptGroup

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from src.common.mapa_unico import MapaUnico
    from workspaces.physics_m3.modules.logging_wal import WALogger
except ImportError:
    MapaUnico = None
    WALogger = None

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.thermo.coupling import ThermalStructuralCoupler


def run_topopt(
    nelx: int = 80,
    nely: int = 40,
    vol_frac: float = 0.3,
    penal: float = 3.0,
    max_iter: int = 200,
    tol: float = 1e-4,
    verbose: bool = True,
) -> dict:
    """
    Run topology optimization and return results dictionary.

    Parameters
    ----------
    nelx : int
        Number of elements in x-direction.
    nely : int
        Number of elements in y-direction.
    vol_frac : float
        Target volume fraction (0, 1].
    penal : float
        SIMP penalization power (>= 1).
    max_iter : int
        Maximum optimization iterations.
    tol : float
        Convergence tolerance on compliance change.
    verbose : bool
        Print progress.

    Returns
    -------
    dict with keys:
        density_field : (nelx*nely,) final density array
        compliance_history : list of compliance values
        converged : bool
        iterations : int
    """
    ndof = 2 * (nelx + 1) * (nely + 1)
    nelem = nelx * nely

    # --- M³ Multifisics Integration: Thermal-Structural Coupling ---
    # Simulate operational temperature from fluid (e.g., 350K / ~77C)
    operational_T_K = 350.15 
    coupler = ThermalStructuralCoupler()
    degraded_E0_Pa = coupler.get_degraded_E(operational_T_K)
    
    if verbose:
        print(f"🌡️ Thermal Coupling: Operational T = {operational_T_K}K ➞ Degraded E0 = {degraded_E0_Pa/1e9:.2f} GPa")

    # Build the optimization problem with thermally degraded E0
    prob = om.Problem()
    prob.model = TopOptGroup(nelx=nelx, nely=nely, vol_frac=vol_frac, penal=penal, E0=degraded_E0_Pa)

    # Driver setup
    prob.driver = om.ScipyOptimizeDriver()
    prob.driver.options["optimizer"] = "SLSQP"
    prob.driver.options["maxiter"] = max_iter
    prob.driver.options["tol"] = tol
    prob.driver.options["disp"] = verbose

    # Design variables: density field [0, 1]
    prob.model.add_design_var("density_field", lower=0.0, upper=1.0)

    # Objective: minimize compliance
    prob.model.add_objective("objective.compliance_value")

    # Constraint: volume fraction <= target
    prob.model.add_constraint("constraint.volume_fraction", upper=vol_frac)

    # Setup problem (MUST precede set_val calls)
    prob.setup()

    # Set initial guess — uniform density at volume fraction
    prob.set_val("density_field", np.full(nelem, vol_frac))

    # Set load vector — unit point load at center-top
    load = np.zeros(ndof)
    load[ndof // 2] = -1.0  # downward force at center-top node
    prob.set_val("load_vector", load)

    # Run optimization
    t0 = time.time()
    prob.run_driver()
    elapsed = time.time() - t0

    density = prob.get_val("density_field").copy()
    final_compliance = float(prob.get_val("objective.compliance_value")[0])
    final_vol = float(prob.get_val("constraint.volume_fraction")[0])
    target_vol_frac = vol_frac

    if verbose:
        print("\n=== TopOpt Complete ===")
        print(f"  Iterations: {prob.driver.iter_count}")
        print(f"  Final compliance: {final_compliance:.6e}")
        print(f"  Final volume fraction: {final_vol:.4f} (target: {vol_frac})")
        print(f"  Elapsed: {elapsed:.1f}s")

    # --- M4 & M5 Integration: Logging and Single Source of Truth ---
    try:
        if MapaUnico and WALogger:
            mapa = MapaUnico(project="BIOEOLICA-CORE")
            entry_id = mapa.register(
                domain="mecanica",
                name=f"TopOpt Result ({nelx}x{nely})",
                data={
                    "final_compliance": float(final_compliance),
                    "iterations": prob.driver.iter_count,
                    "target_vol_frac": target_vol_frac
                }
            )
            
            wal = WALogger(log_dir="data/logs/")
            wal.record(
                what="Topology Optimization Execution",
                why="Generate optimal material layout for target volume fraction",
                who="src/topopt/run_optimization.py",
                where=entry_id,
                how={"optimizer": "SLSQP", "elements": nelx * nely},
                domain="mecanica",
                scale="meso"
            )
            print(f"✅ Optimization logged in MapaUnico (ID: {entry_id})")
    except Exception as e:
        print(f"⚠️ Failed to log to MapaUnico/WAL: {e}")

    return {
        "density_field": density,
        "compliance": final_compliance,
        "volume_fraction": final_vol,
        "compliance_history": [],
        "converged": prob.driver.iter_count < max_iter,
        "iterations": prob.driver.iter_count,
        "elapsed_s": elapsed,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Topology optimization with OpenMDAO + SIMP."
    )
    parser.add_argument("--nelx", type=int, default=80, help="Elements in x")
    parser.add_argument("--nely", type=int, default=40, help="Elements in y")
    parser.add_argument("--vol-frac", type=float, default=0.3, help="Volume fraction")
    parser.add_argument("--penal", type=float, default=3.0, help="SIMP penalization")
    parser.add_argument("--max-iter", type=int, default=200, help="Max iterations")
    parser.add_argument("--tol", type=float, default=1e-4, help="Convergence tolerance")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_topopt(
        nelx=args.nelx,
        nely=args.nely,
        vol_frac=args.vol_frac,
        penal=args.penal,
        max_iter=args.max_iter,
        tol=args.tol,
    )
    # Save density field to .npy
    np.save("topopt_result.npy", result["density_field"])
    print("Density field saved to topopt_result.npy")

    # --- Generate Visualization (Mapa de Calor) ---
    try:
        from src.topopt.visualization import plot_density_field
        plot_density_field(
            density_field=result["density_field"], 
            nelx=args.nelx, 
            nely=args.nely, 
            output_path="topopt_result.png"
        )
    except Exception as e:
        print(f"⚠️ Failed to generate visualization: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
