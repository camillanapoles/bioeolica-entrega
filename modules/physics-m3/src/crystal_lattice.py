"""Crystal lattice 3D module — unit cells, Miller indices, symmetry, DAMASK/ASE bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


LATTICE_TYPES = {
    "sc":  {"name": "Simple Cubic",     "a": 1.0, "atoms_per_cell": 1},
    "bcc": {"name": "Body-Centered Cubic","a": 1.0, "atoms_per_cell": 2},
    "fcc": {"name": "Face-Centered Cubic","a": 1.0, "atoms_per_cell": 4},
    "hcp": {"name": "Hexagonal Close-Packed","a": 1.0, "c/a": 1.633, "atoms_per_cell": 2},
}


@dataclass
class CrystalLattice:
    """Crystal lattice with unit cell geometry and symmetry.

    Parameters
    ----------
    lattice_type : str
        One of 'sc', 'bcc', 'fcc', 'hcp'.
    a : float
        Lattice constant in nm.
    c_over_a : float, optional
        c/a ratio for HCP (default 1.633).
    """
    lattice_type: str = "bcc"
    a: float = 1.0
    c_over_a: float = 1.633

    def __post_init__(self):
        if self.lattice_type not in LATTICE_TYPES:
            raise ValueError(f"Unknown lattice: {self.lattice_type}. Choose from {list(LATTICE_TYPES.keys())}")
        self._info = LATTICE_TYPES[self.lattice_type]

    @property
    def name(self) -> str:
        return self._info["name"]

    @property
    def atoms_per_cell(self) -> int:
        return self._info["atoms_per_cell"]

    def unit_cell_atoms(self) -> np.ndarray:
        """Return (N,3) array of fractional atom positions in the unit cell."""
        if self.lattice_type == "sc":
            return np.array([[0, 0, 0]], dtype=float)
        elif self.lattice_type == "bcc":
            return np.array([[0, 0, 0], [0.5, 0.5, 0.5]], dtype=float)
        elif self.lattice_type == "fcc":
            return np.array([
                [0, 0, 0],
                [0.5, 0.5, 0],
                [0.5, 0, 0.5],
                [0, 0.5, 0.5],
            ], dtype=float)
        elif self.lattice_type == "hcp":
            return np.array([
                [0, 0, 0],
                [1/3, 2/3, 0.5],
            ], dtype=float)

    def supercell(self, nx: int, ny: int, nz: int) -> np.ndarray:
        """Generate supercell atom positions in Cartesian coordinates (nm).

        Parameters
        ----------
        nx, ny, nz : int
            Number of unit cells in each direction.

        Returns
        -------
        positions : (N,3) ndarray
            Cartesian coordinates in nm.
        """
        basis = self.unit_cell_atoms()
        cells = []
        sc = self.a if self.lattice_type != "hcp" else self.a
        sx, sy = sc, sc
        sz = self.a * self.c_over_a if self.lattice_type == "hcp" else sc
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    offset = np.array([ix * sx, iy * sy, iz * sz])
                    for atom in basis:
                        pos = offset + atom * np.array([sx, sy, sz])
                        cells.append(pos)
        return np.array(cells)

    def miller_plane(self, h: int, k: int, l: int, size: float = 2.0, n_points: int = 20) -> tuple:
        """Generate points on a Miller-indexed plane (hkl) within the crystal.

        Parameters
        ----------
        h, k, l : int
            Miller indices.
        size : float
            Half-size of the plane (nm).
        n_points : int
            Grid resolution.

        Returns
        -------
        X, Y, Z : ndarray
            Meshgrid of plane coordinates (nm).
        """
        if h == k == l == 0:
            raise ValueError("Miller indices (000) is invalid")
        a_hkl = self.a / np.sqrt(h**2 + k**2 + l**2) if (h + k + l) > 0 else self.a
        normal = np.array([h, k, l], dtype=float)
        normal = normal / np.linalg.norm(normal)
        u = np.array([-normal[1], normal[0], 0]) if abs(normal[0]) + abs(normal[1]) > 1e-10 else np.array([0, -normal[2], normal[1]])
        u = u / np.linalg.norm(u)
        v = np.cross(normal, u)
        lin = np.linspace(-size, size, n_points)
        Xv, Yv = np.meshgrid(lin, lin)
        return (u[0] * Xv + v[0] * Yv + normal[0] * a_hkl,
                u[1] * Xv + v[1] * Yv + normal[1] * a_hkl,
                u[2] * Xv + v[2] * Yv + normal[2] * a_hkl)

    def interplanar_spacing(self, h: int, k: int, l: int) -> float:
        """Interplanar spacing d_hkl in nm."""
        if h == k == l == 0:
            return 0.0
        if self.lattice_type == "hcp":
            c2 = (self.a * self.c_over_a) ** 2
            return 1.0 / np.sqrt(4 * (h**2 + h*k + k**2) / (3 * self.a**2) + l**2 / c2)
        return self.a / np.sqrt(h**2 + k**2 + l**2)

    def primitive_vectors(self) -> np.ndarray:
        """Return (3,3) primitive lattice vectors."""
        a = self.a
        if self.lattice_type == "sc":
            return np.eye(3) * a
        elif self.lattice_type == "bcc":
            return np.array([[-a/2, a/2, a/2], [a/2, -a/2, a/2], [a/2, a/2, -a/2]], dtype=float) * 2
        elif self.lattice_type == "fcc":
            return np.array([[0, a/2, a/2], [a/2, 0, a/2], [a/2, a/2, 0]], dtype=float) * 2
        else:  # hcp
            return np.array([[a, 0, 0], [-a/2, a*np.sqrt(3)/2, 0], [0, 0, a*self.c_over_a]], dtype=float)

    def reciprocal_vectors(self) -> np.ndarray:
        """Return (3,3) reciprocal lattice vectors (nm^-1)."""
        pv = self.primitive_vectors()
        rv = np.linalg.inv(pv).T * 2 * np.pi
        return rv

    def coordination_number(self) -> int:
        """Coordination number for the lattice type."""
        return {"sc": 6, "bcc": 8, "fcc": 12, "hcp": 12}.get(self.lattice_type, 0)

    def packing_fraction(self) -> float:
        """Atomic packing fraction."""
        return {"sc": 0.524, "bcc": 0.680, "fcc": 0.740, "hcp": 0.740}.get(self.lattice_type, 0.0)

    def density_g_cm3(self, atomic_mass: float = 55.845) -> float:
        """Calculate theoretical density in g/cm³.

        Parameters
        ----------
        atomic_mass : float
            Atomic mass in g/mol (default 55.845 for Fe).

        Returns
        -------
        density : float
            Density in g/cm³.
        """
        n_atoms = self.atoms_per_cell
        if self.lattice_type == "hcp":
            vol = self.a**2 * np.sqrt(3) / 2 * self.a * self.c_over_a
        else:
            vol = self.a**3
        vol_cm3 = vol * 1e-21  # nm³ → cm³
        avogadro = 6.022e23
        return n_atoms * atomic_mass / avogadro / vol_cm3

    def plot_supercell(self, nx: int = 3, ny: int = 3, nz: int = 3, plane: Optional[tuple] = None):
        """Plot supercell atoms using matplotlib.

        Parameters
        ----------
        nx, ny, nz : int
            Supercell dimensions.
        plane : tuple, optional
            Miller indices (h,k,l) to overlay.
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")
        atoms = self.supercell(nx, ny, nz)
        ax.scatter(atoms[:, 0], atoms[:, 1], atoms[:, 2], c="blue", s=20, alpha=0.7)
        if plane:
            X, Y, Z = self.miller_plane(*plane)
            ax.plot_surface(X, Y, Z, alpha=0.3, color="red")
        ax.set_xlabel("x (nm)")
        ax.set_ylabel("y (nm)")
        ax.set_zlabel("z (nm)")
        ax.set_title(f"{self.name} Supercell ({nx}×{ny}×{nz})")
        plt.tight_layout()
        return fig
