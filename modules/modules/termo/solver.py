"""
solver.py — Steady-state heat conduction FEM solver.

Solves K·T = Q where:
  K = conductivity matrix
  T = nodal temperature vector
  Q = thermal load vector (flux, convection)

Element: 8-node hexahedral (trilinear) for regular grids.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix
from scipy.sparse.linalg import spsolve

try:
    from .bc import ThermalBC, parse_bc_string
    from .materials import get_material
except ImportError:
    from bc import ThermalBC, parse_bc_string
    from materials import get_material


class ThermalSolver:
    """Steady-state heat conduction FEM solver for regular hexahedral grids."""

    def __init__(self, nx: int = 10, ny: int = 10, nz: int = 10,
                 k: float = 50.0, Lx: float = 1.0, Ly: float = 1.0, Lz: float = 1.0):
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.k = k
        self.Lx = Lx
        self.Ly = Ly
        self.Lz = Lz
        self.n_nodes = (nx + 1) * (ny + 1) * (nz + 1)
        self.n_elem = nx * ny * nz

    def _node_id(self, i: int, j: int, k: int) -> int:
        """Map (i,j,k) grid indices to global node ID."""
        return k * (self.nx + 1) * (self.ny + 1) + j * (self.nx + 1) + i

    def _build_connectivity(self) -> np.ndarray:
        """Build element connectivity array (n_elem × 8)."""
        conn = np.zeros((self.n_elem, 8), dtype=np.int32)
        idx = 0
        for k in range(self.nz):
            for j in range(self.ny):
                for i in range(self.nx):
                    n0 = self._node_id(i, j, k)
                    conn[idx] = [
                        n0,
                        self._node_id(i+1, j, k),
                        self._node_id(i+1, j+1, k),
                        self._node_id(i, j+1, k),
                        self._node_id(i, j, k+1),
                        self._node_id(i+1, j, k+1),
                        self._node_id(i+1, j+1, k+1),
                        self._node_id(i, j+1, k+1),
                    ]
                    idx += 1
        return conn

    def _hex8_conductivity_matrix(self) -> np.ndarray:
        """8×8 element conductivity matrix for a hex using trilinear shape functions.

        Simplified diagonal approximation for regular hex elements.
        In production, use Gauss quadrature integration.
        """
        ke = np.zeros((8, 8))
        # Trilinear hex: diagonal dominance approximation
        for i in range(8):
            ke[i, i] = 1.0
            for j in range(8):
                if i != j:
                    # Adjacent nodes share faces
                    ke[i, j] = -1.0 / 7.0
        return ke

    def solve(self, bc_temperature: dict[int, float] | None = None,
              bc_flux: dict[int, float] | None = None) -> tuple[np.ndarray, bool]:
        """Solve steady-state heat conduction K·T = Q.

        Parameters
        ----------
        bc_temperature : dict[int, float]
            Node_id → temperature (K) for Dirichlet BCs.
        bc_flux : dict[int, float]
            Node_id → heat flux (W/m²) for Neumann BCs.

        Returns
        -------
        temperatures : np.ndarray
            (n_nodes,) temperature array.
        converged : bool
            True if solve succeeded.
        """
        n = self.n_nodes
        bc_t = bc_temperature or {}
        bc_f = bc_flux or {}

        conn = self._build_connectivity()
        ke = self._hex8_conductivity_matrix()

        # Assemble global conductivity matrix
        rows, cols, data = [], [], []
        for elem in range(self.n_elem):
            for i in range(8):
                for j in range(8):
                    rows.append(conn[elem, i])
                    cols.append(conn[elem, j])
                    data.append(self.k * ke[i, j])
        K = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsc()

        # Apply flux BCs → RHS
        f = np.zeros(n)
        for node_id, flux_val in bc_f.items():
            f[node_id] = flux_val

        # Apply temperature BCs (Dirichlet)
        fixed_nodes = list(bc_t.keys())
        free_nodes = [i for i in range(n) if i not in fixed_nodes]

        if fixed_nodes:
            for node_id, temp in bc_t.items():
                f -= K[:, node_id].toarray().ravel() * temp
            K_reduced = K[free_nodes, :][:, free_nodes]
            f_reduced = f[free_nodes]
        else:
            K_reduced = K
            f_reduced = f

        try:
            t_free = spsolve(K_reduced.tocsc(), f_reduced)
        except Exception:
            return np.zeros(n), False

        temps = np.zeros(n)
        if fixed_nodes:
            for node_id, temp in bc_t.items():
                temps[node_id] = temp
            for i, free_id in enumerate(free_nodes):
                temps[free_id] = t_free[i]
        else:
            temps = t_free

        return temps, True

    def compute_gradient(self, temps: np.ndarray) -> np.ndarray:
        """Estimate thermal gradient magnitude per element."""
        conn = self._build_connectivity()
        grad = np.zeros(self.n_elem)
        for e in range(self.n_elem):
            elem_temps = temps[conn[e]]
            grad[e] = np.max(elem_temps) - np.min(elem_temps)
        return grad


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Thermal FEM solver")
    parser.add_argument("--nx", type=int, default=10, help="Elements in x")
    parser.add_argument("--ny", type=int, default=10, help="Elements in y")
    parser.add_argument("--nz", type=int, default=10, help="Elements in z")
    parser.add_argument("--k", type=float, default=50.0, help="Conductivity W/mK")
    parser.add_argument("--bc-temp", type=str, default="",
                        help="Node:Temp e.g. '0:300,1330:400'")
    parser.add_argument("--bc-flux", type=str, default="",
                        help="Node:Flux e.g. '100:1000'")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    solver = ThermalSolver(nx=args.nx, ny=args.ny, nz=args.nz, k=args.k)
    bc_t = parse_bc_string(args.bc_temp) if args.bc_temp else {}
    bc_f = parse_bc_string(args.bc_flux) if args.bc_flux else {}
    temps, converged = solver.solve(bc_t, bc_f)
    if converged:
        print(f"Solve OK: min={temps.min():.1f}K max={temps.max():.1f}K")
        np.save("temperature_field.npy", temps)
    else:
        print("Solve FAILED")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
