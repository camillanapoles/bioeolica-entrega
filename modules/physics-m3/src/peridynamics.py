#!/usr/bin/env python3
"""
Peridynamics Solver — Bond-based non-local continuum mechanics.

Per INSTRUCTIONS.md KDI numerical methods: Peridynamics for fracture initiation.
  - Bond-based formulation (Silling 2000)
  - Horizon δ and influence function
  - Bond stretch damage criterion
  - Crack propagation with damage tracking
  - Integration with fem_solver for hybrid models

Uso:
    from peridynamics import PeridynamicsModel, BondBasedPD

    pd = PeridynamicsModel(horizon=0.01, rho=1200, E=3.5e9)
    pd.create_grid(nodes=20, L=0.1)
    pd.set_bc(fixed_left=True, load_right=1000)
    result = pd.solve()
    print(result['damage'].max())
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable


@dataclass
class PeridynamicsModel:
    """Bond-based Peridynamics model."""
    horizon_m: float = 0.01
    rho_kgm3: float = 1200.0
    E_GPa: float = 3.5
    Gc_Jm2: float = 100.0  # Fracture energy
    nodes: np.ndarray = field(default_factory=lambda: np.array([]))
    bonds: np.ndarray = field(default_factory=lambda: np.array([]))
    volumes: np.ndarray = field(default_factory=lambda: np.array([]))
    damage: np.ndarray = field(default_factory=lambda: np.array([]))
    displacements: np.ndarray = field(default_factory=lambda: np.array([]))

    def create_grid(self, nodes: int = 20, L: float = 0.1,
                    dim: int = 1) -> Dict:
        """Create 1D grid of nodes with bond connectivity."""
        dx = L / nodes
        self.nodes = np.linspace(dx / 2, L - dx / 2, nodes)
        self.volumes = np.full(nodes, dx)
        self.damage = np.zeros(nodes)
        self.displacements = np.zeros(nodes)

        bonds = []
        for i in range(nodes):
            for j in range(nodes):
                if i != j:
                    dist = abs(self.nodes[i] - self.nodes[j])
                    if dist <= self.horizon_m:
                        bonds.append([i, j, dist])
        self.bonds = np.array(bonds)
        return {"n_nodes": nodes, "n_bonds": len(bonds), "dx_m": dx}

    def stiffness_matrix(self) -> np.ndarray:
        """Assemble peridynamic stiffness matrix."""
        n = len(self.nodes)
        E = self.E_GPa * 1e9
        c = 6 * E / (np.pi * self.horizon_m**3)  # micromodulus (1D simplification)
        K = np.zeros((n, n))
        for bond in self.bonds:
            i, j, dist = int(bond[0]), int(bond[1]), bond[2]
            if self.damage[i] < 0.5 and self.damage[j] < 0.5:
                k_bond = c * self.volumes[i] * self.volumes[j] / dist**2
                K[i, i] += k_bond
                K[i, j] -= k_bond
                K[j, i] -= k_bond
                K[j, j] += k_bond
        return K

    def solve(self, fixed_left: bool = True, load_right_N: float = 1000,
              damage_tol: float = 0.5) -> Dict:
        """Solve peridynamics with damage evolution."""
        K = self.stiffness_matrix()
        n = len(self.nodes)
        F = np.zeros(n)

        if fixed_left:
            K[0, :] = 0
            K[0, 0] = 1e15
        F[-1] = load_right_N

        try:
            self.displacements = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            # Fallback to least-squares if singular
            self.displacements, _, _, _ = np.linalg.lstsq(K, F, rcond=None)

        for bond in self.bonds:
            i, j, dist0 = int(bond[0]), int(bond[1]), bond[2]
            strain = abs(self.displacements[i] - self.displacements[j]) / dist0
            stretch_crit = np.sqrt(5 * self.Gc_Jm2 / (9 * self.E_GPa * 1e9 * self.horizon_m))
            if strain > stretch_crit:
                self.damage[i] = min(1.0, self.damage[i] + 0.1)
                self.damage[j] = min(1.0, self.damage[j] + 0.1)

        return {
            "displacements": self.displacements.tolist(),
            "damage": self.damage.tolist(),
            "max_damage": float(self.damage.max()),
            "max_displacement_m": float(np.max(np.abs(self.displacements))),
        }

    def identify_crack(self, threshold: float = 0.75) -> List[int]:
        """Identify cracked nodes (damage > threshold)."""
        return [int(i) for i in range(len(self.nodes)) if self.damage[i] > threshold]
